import streamlit as st
from dotenv import load_dotenv
import pyttsx3
import whisper
import requests
import os
from openai import OpenAI
import logging
logging.basicConfig(filename="app_errors.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()

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

# If OpenAI, ask for API key
openai_key = ""
if use_openai:
    openai_key = os.getenv("OPENAI_API_KEY")
if use_openai and not openai_key:
    st.warning("🔐 API key not found in .env file.")

#validating if ollama is running
if not use_openai:
    try:
        res = requests.get("http://localhost:11434")
    except:
        st.error("⚠️ Ollama is not running. Please run `ollama run mistral` in a terminal.")
# Upload audio
uploaded_audio = st.file_uploader("🎙️ Upload meeting audio", type=["mp3", "wav", "m4a"])

if uploaded_audio:
    with st.spinner("🔄 Transcribing..."):
        ext = uploaded_audio.name.split('.')[-1]
        audio_path = f"temp.{ext}"
        with open(audio_path, "wb") as f:
            f.write(uploaded_audio.read())
        try:
            result = whisper_model.transcribe(audio_path)
            user_text = result['text'].strip()
        except Exception as e:
            st.error(f"❌ Transcription failed: {e}")
            logging.error("Transcription Error: %s", e)
            
        os.remove(audio_path)

        
        st.text_area("🎧 Transcript:", user_text, height=150)

        # Respond with selected LLM
        with st.spinner("🤖 Generating reply..."):
            if use_openai:
                try:
                    client = OpenAI(api_key=openai_key)
                    completion = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant in a meeting."},
                            {"role": "user", "content": user_text}
                        ]
                    )
                    reply = completion.choices[0].message.content
                except Exception as e:
                    st.error(f"OpenAI Error: {e}")
                    logging.error("OpenAI Error: %s", e)
                    reply = "⚠️ Could not get a response from OpenAI."
            else:
                try:
                    res = requests.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": "mistral",  # Change to "llama2", etc. if needed
                            "prompt": f"You are an assistant in a meeting. Respond to this: {user_text}",
                            "stream": False
                        }
                    )
                    res.raise_for_status() #raise error for HTTP issues
                    reply = res.json().get("response", "⚠️ No response from local model.")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Ollama API Error: {e}")
                    logging.error("Ollama API Error: %s", e)
                    reply = "⚠️ Failed to get response from Ollama."
                except Exception as e:
                    st.error(f"Ollama Error: {e}")
                    logging.error("Ollama Unexpected Error: %s", e)
                    reply = "⚠️ Could not get a response from Ollama."

        # Save conversation
        st.session_state.history.append({"role": "user", "content": user_text})
        st.session_state.history.append({"role": "assistant", "content": reply})

        st.success("🤖 Assistant:")
        st.write(reply)

        # Text-to-speech (TTS)
        if st.button("🔊 Speak it"):
            try:
                tts_engine.say(reply)
                tts_engine.runAndWait()
            except Exception as e:
                st.error(f"🔇 TTS Error: {e}")
                logging.error("TTS Error: %s", e)

# Show chat history
if st.session_state.history:
    with st.expander("🗂️ Conversation History"):
        for msg in st.session_state.history:
            role = "🧑 You" if msg["role"] == "user" else "🤖 Assistant"
            st.markdown(f"**{role}:** {msg['content']}")
