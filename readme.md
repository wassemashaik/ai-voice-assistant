# 🧠 AI Voice Assistant Agent

A smart AI-powered assistant that can **transcribe meeting audio**, **respond intelligently**, and even **speak its replies aloud** — as if it attended the meeting on your behalf.

Built using **Python**, **Streamlit**, **Whisper**, **OpenAI GPT-3.5** or **Local LLMs (via Ollama)**, and **Text-to-Speech**.

---

## 🚀 Features

- 🎙️ Upload meeting audio (`.mp3`, `.wav`, `.m4a`)
- 🧠 Transcribes using [OpenAI Whisper](https://github.com/openai/whisper)
- 🤖 Responds using:
  - OpenAI GPT-3.5 (cloud)
  - Mistral via Ollama (local)
- 🔊 Converts response to speech (TTS)
- 💬 Conversation history tracking

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

## 🛠️ Installation

1. Clone the repo:
   ```bash
   git clone https://github.com/wassemashaik/ai-voice-assistant.git
   cd ai-voice-assistant


![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Streamlit](https://img.shields.io/badge/Made%20with-Streamlit-orange?logo=streamlit)
![Open Issues](https://img.shields.io/github/issues/wassemashaik/ai-voice-assistant)
![Last Commit](https://img.shields.io/github/last-commit/wassemashaik/ai-voice-assistant)
![Stars](https://img.shields.io/github/stars/wassemashaik/ai-voice-assistant?style=social)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)


to activate ollma server you should ollama run mistral

to activate virtual enviroment of python you should streamlit run voice_assistant.py

Features added:
- 

things to do: