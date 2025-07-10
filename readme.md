# 🧠 Voice Assistant Agent

A smart AI-powered assistant that can **transcribe meeting audio**, **respond intelligently**, and even **speak its replies aloud** — as if it attended the meeting on your behalf.

Built using **Python**, **Streamlit**, **Whisper**, **OpenAI GPT-3.5** or **Local LLMs (via Ollama)**, and **Text-to-Speech**.

---

## 🎯 Features

- 🎙️ Upload meeting audio (MP3, WAV, M4A)
- 📝 Transcribe audio using OpenAI’s Whisper
- 🤖 Smart reply generation (OpenAI GPT-3.5 or local model via Ollama)
- 🔊 Converts AI replies to speech using pyttsx3
- 🗂️ Saves and displays conversation history
- ⚙️ Built-in error handling for API and transcription issues
- 🧪 Easy to switch between local and cloud models

---

## 📦 Tech Stack

| Tool        | Role                                |
|-------------|-------------------------------------|
| Python      | Core language                       |
| Streamlit   | UI framework                        |
| Whisper     | Audio transcription                 |
| OpenAI API  | GPT-3.5-based chat assistant        |
| Ollama      | Local LLM runner (e.g., Mistral)    |
| pyttsx3     | Text-to-speech                      |
| dotenv      | Secure API key loading              |
| requests    | API calls to local model server     |

---


to activate ollma server you should ollama run mistral

to activate virtual enviroment of python you should streamlit run voice_assistant.py

Features added:
- 

things to do: