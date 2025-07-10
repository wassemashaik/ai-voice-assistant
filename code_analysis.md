# Voice Assistant Code Analysis - Bugs and Fixes

## Identified Bugs and Issues

### 1. **Audio Processing Sample Rate Mismatch**
**Bug**: The `save_audio()` function hardcodes sample rate to 48000, but WebRTC audio frames may have different sample rates.

**Fix**: Get the actual sample rate from the audio frame:
```python
def save_audio(frames, sample_rate):  # Remove default parameter
    # ... rest of function
```

### 2. **Audio Format Conversion Issues**
**Bug**: WebRTC audio frames are typically in float32 format (-1.0 to 1.0), but the code directly converts to int16 without proper scaling.

**Fix**: Properly convert float32 to int16:
```python
def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
    audio = frame.to_ndarray()
    # Store both audio data and sample rate
    self.frames.append({
        'data': audio,
        'sample_rate': frame.sample_rate,
        'channels': len(audio.shape) if len(audio.shape) > 1 else 1
    })
    return frame

def save_audio(frame_data_list):
    if not frame_data_list:
        return None
        
    # Get sample rate from first frame
    sample_rate = frame_data_list[0]['sample_rate']
    
    temp_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    with wave.open(temp_path, "wb") as wf:
        wf.setnchannels(1)  # Convert to mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        
        for frame_info in frame_data_list:
            audio_data = frame_info['data']
            
            # Convert to mono if stereo
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Convert float32 to int16 properly
            if audio_data.dtype == np.float32:
                audio_data = (audio_data * 32767).astype(np.int16)
            elif audio_data.dtype != np.int16:
                audio_data = audio_data.astype(np.int16)
                
            wf.writeframes(audio_data.tobytes())
    return temp_path
```

### 3. **TTS Engine Thread Safety Issues**
**Bug**: Global TTS engine initialization can cause issues in multi-user Streamlit environments.

**Fix**: Initialize TTS engine per function call:
```python
def speak_text(text):
    try:
        # Initialize TTS engine locally to avoid threading issues
        local_tts_engine = pyttsx3.init()
        local_tts_engine.say(text)
        local_tts_engine.runAndWait()
    except Exception as e:
        log_and_alert_error("TTS", e)
```

### 4. **Audio Buffer Management**
**Bug**: Clearing frames from the audio processor doesn't work reliably due to WebRTC's asynchronous nature.

**Fix**: Implement proper buffer management:
```python
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.frames = []
        self.recording = True

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        if self.recording:
            audio = frame.to_ndarray()
            self.frames.append({
                'data': audio,
                'sample_rate': frame.sample_rate
            })
        return frame
    
    def stop_recording(self):
        self.recording = False
    
    def clear_frames(self):
        self.frames.clear()
        self.recording = True
```

### 5. **Error Handling for Model Loading**
**Bug**: Whisper model loading can fail but isn't properly handled.

**Fix**: Add proper error handling:
```python
# Load models with error handling
try:
    whisper_model = whisper.load_model("base")
except Exception as e:
    st.error(f"Failed to load Whisper model: {e}")
    st.stop()
```

### 6. **File Cleanup Issues**
**Bug**: Temporary files might not be cleaned up if exceptions occur.

**Fix**: Use context managers or try-finally blocks:
```python
def transcribe_audio(audio_path):
    try:
        result = whisper_model.transcribe(audio_path)
        return result['text'].strip()
    except Exception as e:
        log_and_alert_error("Transcription", e)
        return None
    finally:
        # Ensure cleanup happens
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass
```

### 7. **Missing Dependencies Check**
**Bug**: The code doesn't check if required dependencies are installed.

**Fix**: Add dependency checks:
```python
def check_dependencies():
    missing_deps = []
    
    try:
        import streamlit_webrtc
    except ImportError:
        missing_deps.append("streamlit-webrtc")
    
    try:
        import whisper
    except ImportError:
        missing_deps.append("openai-whisper")
    
    try:
        import pyttsx3
    except ImportError:
        missing_deps.append("pyttsx3")
    
    if missing_deps:
        st.error(f"Missing dependencies: {', '.join(missing_deps)}")
        st.info("Install with: pip install " + " ".join(missing_deps))
        st.stop()

# Call at the beginning
check_dependencies()
```

### 8. **WebRTC Context State Management**
**Bug**: The WebRTC context state isn't properly managed, leading to potential issues with stopping/starting recording.

**Fix**: Improve state management:
```python
# In the recording section:
if ctx and ctx.audio_processor:
    if ctx.state.playing:
        st.info("🎤 Recording... Press 'Stop and Transcribe' when ready.")
        if st.button("⏹️ Stop and Transcribe"):
            ctx.audio_processor.stop_recording()
            if ctx.audio_processor.frames:
                audio_path = save_audio(ctx.audio_processor.frames)
                if audio_path:
                    user_text = transcribe_audio(audio_path)
                    if user_text:
                        handle_transcript(user_text, openai_key, use_openai)
                ctx.audio_processor.clear_frames()
    else:
        st.info("Press 'START' to begin recording")
```

### 9. **OpenAI API Key Validation**
**Bug**: The code doesn't validate if the OpenAI API key is valid before making requests.

**Fix**: Add API key validation:
```python
def validate_openai_key(api_key):
    if not api_key:
        return False
    try:
        client = OpenAI(api_key=api_key)
        # Test with a minimal request
        client.models.list()
        return True
    except Exception:
        return False

# In main code:
if use_openai and not validate_openai_key(openai_key):
    st.error("🔐 Invalid or missing OpenAI API key.")
    st.stop()
```

### 10. **Memory Management**
**Bug**: Large audio files can cause memory issues as frames are stored in memory.

**Fix**: Implement streaming to disk:
```python
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        self.wave_writer = None
        self.recording = True

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        if self.recording:
            if self.wave_writer is None:
                self.wave_writer = wave.open(self.temp_file.name, "wb")
                self.wave_writer.setnchannels(1)
                self.wave_writer.setsampwidth(2)
                self.wave_writer.setframerate(frame.sample_rate)
            
            audio = frame.to_ndarray()
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
            if audio.dtype == np.float32:
                audio = (audio * 32767).astype(np.int16)
            
            self.wave_writer.writeframes(audio.tobytes())
        return frame
```

## Complete Fixed Code Structure

The main issues to address:
1. Proper audio format handling
2. Sample rate detection and conversion
3. Thread-safe TTS initialization
4. Better error handling and cleanup
5. Memory management for large audio files
6. Proper WebRTC state management
7. Dependency validation

These fixes will make your voice assistant more robust and handle edge cases better.