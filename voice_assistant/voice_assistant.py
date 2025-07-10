import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
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
import threading
logging.basicConfig(filename="app_errors.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()

# Improved AudioProcessor with proper state management
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.lock = threading.Lock()
        
    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        with self.lock:
            audio = frame.to_ndarray()
            # Properly store frames in session state
            if "audio_frames" not in st.session_state:
                st.session_state.audio_frames = []
            st.session_state.audio_frames.append(audio)
        return frame

def save_audio(frames, sample_rate=48000):
    """Convert audio frames to WAV file"""
    temp_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    with wave.open(temp_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for frame in frames:
            # Ensure proper data type conversion
            audio_data = np.array(frame, dtype=np.float32)
            # Normalize to int16 range
            audio_data = np.clip(audio_data * 32767, -32768, 32767).astype(np.int16)
            wf.writeframes(audio_data.tobytes())
    return temp_path

def transcribe_audio(audio_path):
    try:
        result = whisper_model.transcribe(audio_path)
        return result['text'].strip()
    except Exception as e:
        log_and_alert_error("Transcription", e)
        return None
   
def get_openai_response(prompt, api_key):
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
    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": f"You are an assistant in a meeting. Respond to this: {prompt}",
                "stream": False
            }
        )
        res.raise_for_status()
        return res.json().get("response", "⚠️ No response from local model.")
    except Exception as e:
        log_and_alert_error("Ollama", e)
        return "⚠️ Could not get a response from Ollama."

def speak_text(text):
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception as e:
        log_and_alert_error("TTS", e)

def log_and_alert_error(source, exception):
    st.error(f"{source} Error: {exception}")
    logging.error(f"{source} Error: %s", exception)

def handle_transcript(user_text, openai_key, use_openai):
    st.text_area("🎧 Transcript:", user_text, height=150)
    with st.spinner("🤖 Generating reply..."):
        reply = get_openai_response(user_text, openai_key) if use_openai else get_ollama_response(user_text)

    st.session_state.history.append({"role": "user", "content": user_text})
    st.session_state.history.append({"role": "assistant", "content": reply})

    st.success("🤖 Assistant:")
    st.write(reply)

    if st.button("🔊 Speak it"):
        speak_text(reply)

def process_recorded_audio():
    """Process recorded audio frames and transcribe"""
    if "audio_frames" in st.session_state and st.session_state.audio_frames:
        try:
            with st.spinner("🔄 Processing audio..."):
                # Save audio frames to file
                audio_path = save_audio(st.session_state.audio_frames)
                
                # Transcribe audio
                user_text = transcribe_audio(audio_path)
                
                # Clean up
                os.remove(audio_path)
                st.session_state.audio_frames = []  # Clear frames
                
                if user_text:
                    return user_text
                else:
                    st.error("❌ Could not transcribe audio. Please try again.")
                    return None
        except Exception as e:
            log_and_alert_error("Audio Processing", e)
            return None
    else:
        st.warning("⚠️ No audio frames recorded. Please record some audio first.")
        return None

# Streamlit config
st.set_page_config(page_title="🧠 Voice Assistant Agent", layout="centered")
st.title("🧠 Voice Assistant Agent")

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "audio_frames" not in st.session_state:
    st.session_state.audio_frames = []
if "recording_state" not in st.session_state:
    st.session_state.recording_state = "stopped"

# Load models
try:
    tts_engine = pyttsx3.init()
    whisper_model = whisper.load_model("base")
except Exception as e:
    st.error(f"❌ Failed to initialize models: {e}")
    st.stop()

# 🔁 Model selection
model_choice = st.radio("Choose LLM:", ["💻 Local (Ollama)", "☁️ OpenAI GPT-3.5"])
use_openai = model_choice == "☁️ OpenAI GPT-3.5"
openai_key = os.getenv("OPENAI_API_KEY") if use_openai else ""

# If OpenAI, ask for API key
if use_openai and not openai_key:
    st.warning("🔐 API key not found in .env file.")
elif not use_openai:
    try:
        requests.get("http://localhost:11434", timeout=5)
    except requests.exceptions.RequestException:
        st.error("⚠️ Ollama is not running. Please run `ollama run mistral` in a terminal.")

# Recording section
st.markdown("### 🎙️ Record Audio")

# WebRTC streamer with improved configuration
webrtc_ctx = webrtc_streamer(
    key="audio-recorder",
    mode=WebRtcMode.SENDONLY,
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={
        "audio": {
            "echoCancellation": True,
            "noiseSuppression": True,
            "sampleRate": 48000,
        },
        "video": False
    },
    async_processing=True,
    sendback_audio=False
)

# Recording controls with improved state management
col1, col2 = st.columns(2)

with col1:
    if webrtc_ctx.state.playing:
        st.success("🎤 Recording in progress...")
        st.session_state.recording_state = "recording"
    elif st.session_state.recording_state == "recording":
        st.session_state.recording_state = "stopped"
        st.info("🛑 Recording stopped. Click 'Transcribe' to process.")

with col2:
    if st.button("⏹️ Stop and Transcribe", disabled=not (st.session_state.audio_frames)):
        user_text = process_recorded_audio()
        if user_text:
            handle_transcript(user_text, openai_key, use_openai)

# Show recording status
if st.session_state.audio_frames:
    st.info(f"📊 Recorded {len(st.session_state.audio_frames)} audio frames")

# Upload audio
st.markdown("### 📁 Upload Audio File")
uploaded_audio = st.file_uploader("🎙️ Upload meeting audio", type=["mp3", "wav", "m4a"])

if uploaded_audio:
    with st.spinner("🔄 Transcribing..."):
        ext = uploaded_audio.name.split('.')[-1]
        audio_path = f"temp.{ext}"
        with open(audio_path, "wb") as f:
            f.write(uploaded_audio.read())
        
        user_text = transcribe_audio(audio_path)
        os.remove(audio_path)

    if user_text:
        handle_transcript(user_text, openai_key, use_openai)

# Show chat history
if st.session_state.history:
    with st.expander("🗂️ Conversation History"):
        for msg in st.session_state.history:
            role = "🧑 You" if msg["role"] == "user" else "🤖 Assistant"
            st.markdown(f"**{role}:** {msg['content']}")

# Debug section (can be removed in production)
if st.checkbox("🔧 Debug Info"):
    st.write("**WebRTC State:**", webrtc_ctx.state if webrtc_ctx else "None")
    st.write("**Audio Frames Count:**", len(st.session_state.audio_frames))
    st.write("**Recording State:**", st.session_state.recording_state)

