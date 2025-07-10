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
logging.basicConfig(filename="app_errors.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()
# adding live audio 
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.frames = []
        if "audio_frames" not in st.session_state:
            st.session_state.audio_frames = []
    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray()
        self.session_state.audio_frames.append(audio)
        return frame
    
def save_audio(frames, sample_rate=48000):
    temp_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    with wave.open(temp_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for frame in frames:
            wf.writeframes(frame.astype(np.int16).tobytes())
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

# Streamlit config
st.set_page_config(page_title="🧠 Voice Assistant Agent", layout="centered")
st.title("🧠 Voice Assistant Agent")

# Load models
tts_engine = pyttsx3.init()
whisper_model = whisper.load_model("base")

# Session state for chat
if "history" not in st.session_state:
    st.session_state.history = []

# 🔁 Model selection
model_choice = st.radio("Choose LLM:", ["💻 Local (Ollama)", "☁️ OpenAI GPT-3.5"])
use_openai = model_choice == "☁️ OpenAI GPT-3.5"
openai_key = os.getenv("OPENAI_API_KEY") if use_openai else ""

# If OpenAI, ask for API key
if use_openai and not openai_key:
    st.warning("🔐 API key not found in .env file.")
elif not use_openai:
    try:
        requests.get("http://localhost:11434")
    except requests.exceptions.RequestException:
        st.error("⚠️ Ollama is not running. Please run `ollama run mistral` in a terminal.")
#recording
st.markdown("### 🎙️ Record Audio")

ctx = webrtc_streamer(
    key="audio",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
    sendback_audio=False
)

if ctx and ctx.audio_processor:
    st.info("🎤 Recording... Press 'Stop and Transcribe' when ready.")
    if st.button("⏹️ Stop and Transcribe"):
        if "audio_frames" in st.session_state and st.session_state.audio_frames:
            audio_path = save_audio(ctx.audio_processor.frames)
            user_text = transcribe_audio(audio_path)
            os.remove(audio_path)
        
            ctx.audio_processor.frames.clear()
        
            if user_text:
                handle_transcript(user_text, openai_key, use_openai)
    else:
        st.warning("⚠️ No audio frames were recorded. Try again.")


# Upload audio
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

