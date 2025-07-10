import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av
import numpy as np
import wave
import tempfile
from dotenv import load_dotenv
import pyttsx3
import whisper
import requests
import os
from openai import OpenAI
import logging

# Setup logging
logging.basicConfig(filename="app_errors.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()

def check_dependencies():
    """Check if all required dependencies are installed"""
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

# Check dependencies first
check_dependencies()

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.frames = []
        self.recording = True
        self.sample_rate = None

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        if self.recording:
            audio = frame.to_ndarray()
            # Store audio data with metadata
            self.frames.append({
                'data': audio,
                'sample_rate': frame.sample_rate,
                'channels': len(audio.shape) if len(audio.shape) > 1 else 1
            })
            # Store sample rate from first frame
            if self.sample_rate is None:
                self.sample_rate = frame.sample_rate
        return frame
    
    def stop_recording(self):
        self.recording = False
    
    def clear_frames(self):
        self.frames.clear()
        self.recording = True
        self.sample_rate = None

def save_audio(frame_data_list):
    """Save audio frames to a WAV file with proper format conversion"""
    if not frame_data_list:
        return None
        
    # Get sample rate from first frame
    sample_rate = frame_data_list[0]['sample_rate']
    
    temp_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    
    try:
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
                    # Scale from [-1, 1] to [-32767, 32767]
                    audio_data = np.clip(audio_data * 32767, -32767, 32767).astype(np.int16)
                elif audio_data.dtype != np.int16:
                    audio_data = audio_data.astype(np.int16)
                    
                wf.writeframes(audio_data.tobytes())
        return temp_path
    except Exception as e:
        log_and_alert_error("Audio Save", e)
        return None

def transcribe_audio(audio_path):
    """Transcribe audio using Whisper with proper error handling"""
    try:
        result = whisper_model.transcribe(audio_path)
        return result['text'].strip()
    except Exception as e:
        log_and_alert_error("Transcription", e)
        return None
    finally:
        # Ensure cleanup happens
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass

def validate_openai_key(api_key):
    """Validate OpenAI API key"""
    if not api_key:
        return False
    try:
        client = OpenAI(api_key=api_key)
        # Test with a minimal request
        client.models.list()
        return True
    except Exception:
        return False
   
def get_openai_response(prompt, api_key):
    """Get response from OpenAI with proper error handling"""
    try:
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {"role": "system", "content": "You are a exceptionally talented assistant in a meeting"},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        log_and_alert_error("OpenAI", e)
        return "⚠️ Could not get a response from OpenAI."

def get_ollama_response(prompt):
    """Get response from Ollama with proper error handling"""
    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": f"You are an assistant in a meeting. Respond to this: {prompt}",
                "stream": False
            },
            timeout=30  # Add timeout
        )
        res.raise_for_status()
        return res.json().get("response", "⚠️ No response from local model.")
    except Exception as e:
        log_and_alert_error("Ollama", e)
        return "⚠️ Could not get a response from Ollama."

def speak_text(text):
    """Convert text to speech with thread safety"""
    try:
        # Initialize TTS engine locally to avoid threading issues
        local_tts_engine = pyttsx3.init()
        local_tts_engine.say(text)
        local_tts_engine.runAndWait()
    except Exception as e:
        log_and_alert_error("TTS", e)

def log_and_alert_error(source, exception):
    """Log errors and display to user"""
    error_msg = f"{source} Error: {exception}"
    st.error(error_msg)
    logging.error(error_msg)

def handle_transcript(user_text, openai_key, use_openai):
    """Handle transcribed text and generate response"""
    st.text_area("🎧 Transcript:", user_text, height=150)
    
    with st.spinner("🤖 Generating reply..."):
        if use_openai:
            reply = get_openai_response(user_text, openai_key)
        else:
            reply = get_ollama_response(user_text)

    # Update session state
    if "history" not in st.session_state:
        st.session_state.history = []
        
    st.session_state.history.append({"role": "user", "content": user_text})
    st.session_state.history.append({"role": "assistant", "content": reply})

    st.success("🤖 Assistant:")
    st.write(reply)

    # TTS button
    if st.button("🔊 Speak it", key=f"speak_{len(st.session_state.history)}"):
        speak_text(reply)

# Streamlit config
st.set_page_config(page_title="🧠 Voice Assistant Agent", layout="centered")
st.title("🧠 Voice Assistant Agent")

# Load models with error handling
@st.cache_resource
def load_whisper_model():
    try:
        return whisper.load_model("base")
    except Exception as e:
        st.error(f"Failed to load Whisper model: {e}")
        st.stop()

whisper_model = load_whisper_model()

# Session state for chat
if "history" not in st.session_state:
    st.session_state.history = []

# Model selection
model_choice = st.radio("Choose LLM:", ["💻 Local (Ollama)", "☁️ OpenAI GPT-3.5"])
use_openai = model_choice == "☁️ OpenAI GPT-3.5"
openai_key = os.getenv("OPENAI_API_KEY") if use_openai else ""

# Validate setup
if use_openai:
    if not openai_key:
        st.warning("🔐 API key not found in .env file.")
        st.stop()
    elif not validate_openai_key(openai_key):
        st.error("🔐 Invalid OpenAI API key.")
        st.stop()
else:
    try:
        response = requests.get("http://localhost:11434", timeout=5)
        if response.status_code != 200:
            raise requests.exceptions.RequestException()
    except requests.exceptions.RequestException:
        st.error("⚠️ Ollama is not running. Please run `ollama run mistral` in a terminal.")
        st.stop()

# Recording section
st.markdown("### 🎙️ Record Audio")

ctx = webrtc_streamer(
    key="audio",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
    sendback_audio=False
)

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
                
                # Clear frames after processing
                ctx.audio_processor.clear_frames()
            else:
                st.warning("No audio data recorded. Please try again.")
    else:
        st.info("Press 'START' to begin recording")

# Upload audio section
st.markdown("### 📁 Upload Audio File")
uploaded_audio = st.file_uploader("🎙️ Upload meeting audio", type=["mp3", "wav", "m4a"])

if uploaded_audio:
    with st.spinner("🔄 Transcribing..."):
        # Get file extension
        ext = uploaded_audio.name.split('.')[-1]
        audio_path = f"temp_{uploaded_audio.name}"
        
        try:
            # Save uploaded file
            with open(audio_path, "wb") as f:
                f.write(uploaded_audio.read())
            
            # Transcribe
            user_text = transcribe_audio(audio_path)
            
            if user_text:
                handle_transcript(user_text, openai_key, use_openai)
            else:
                st.error("Could not transcribe the audio file. Please check the file format.")
                
        except Exception as e:
            log_and_alert_error("File Upload", e)
        finally:
            # Clean up uploaded file
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except:
                    pass

# Show chat history
if st.session_state.history:
    with st.expander("🗂️ Conversation History"):
        for i, msg in enumerate(st.session_state.history):
            role = "🧑 You" if msg["role"] == "user" else "🤖 Assistant"
            st.markdown(f"**{role}:** {msg['content']}")
            
            # Add separator between conversations
            if i < len(st.session_state.history) - 1:
                st.markdown("---")

# Add clear history button
if st.session_state.history:
    if st.button("🗑️ Clear Conversation History"):
        st.session_state.history = []
        st.rerun()