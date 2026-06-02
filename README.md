<div align="center">

# 🤖 AI Assistant Unlimited

### A free, private, local AI assistant with a built-in app builder.

Chat with a local AI, **describe an app in plain English**, watch it build in a
**live preview**, edit the files, and **download it as a ZIP** — all running on your
own machine with no external accounts required.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-web%20app-000000?logo=flask&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-local%20AI-000000?logo=ollama&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e)
![Privacy](https://img.shields.io/badge/Privacy-100%25%20local-7c6cff)

**Made with 🍃 by MangliJuliano**

</div>

---

## ✨ Features

- 💬 **Chat mode** — ask coding questions, get explanations and debugging help.
- 🔨 **Build mode** — describe an app and the AI writes the code for you.
- 👁️ **Live preview** — see your generated app render instantly in a browser pane.
- 📂 **Project workspace** — browse and edit every generated file in a built-in editor.
- 📦 **One-click ZIP** — download your whole project as a folder to keep or run anywhere.
- 🌐 **Real-time web search** — optional DuckDuckGo/Brave lookups for current info.
- 🔒 **100% private & local** — the AI runs on your machine; chats aren't sent to third parties.
- 💸 **Free to run** — no API keys, no per-message fees (runs on open models via Ollama).

---

## 🚀 Quick Start

### 1. Prerequisites
- [Python 3.11+](https://www.python.org/)
- [Ollama](https://ollama.com/) installed and available on your PATH

### 2. Install
```bash
git clone https://github.com/MangliJuliano/ai-assistant-unlimited.git
cd ai-assistant-unlimited
pip install -r requirements.txt
```

### 3. Pull a model
```bash
# Lightweight, fast (good on ~8GB RAM)
ollama pull qwen2.5-coder:3b

# Smarter, needs more RAM (~16GB+)
ollama pull qwen2.5-coder:7b
```

### 4. Run
```bash
# Terminal 1 — start the AI engine
ollama serve

# Terminal 2 — start the app
python app.py
```

Then open **http://localhost:5000** in your browser. 🎉

---

## 🧠 How to use it

| Action | What it does |
| --- | --- |
| **Chat** | Ask anything — code help, explanations, debugging. |
| **Build** | Describe an app ("build a calculator") — the AI generates it live. |
| **Preview tab** | See your app render in real time. |
| **Code tab** | View and edit the generated files, then save. |
| **ZIP button** | Download the whole project. |
| **New button** | Start a fresh project. |
| **Model dropdown** | Switch between installed AI models. |

---

## ⚙️ Configuration

Set these as environment variables (all optional):

| Variable | Default | Description |
| --- | --- | --- |
| `DEFAULT_MODEL` | `qwen2.5-coder:3b` | Ollama model to use. |
| `ENABLE_WEB_SEARCH` | `True` | Toggle real-time web search. |
| `ENABLE_VERSION_CHECK` | `True` | Toggle package version lookups. |
| `MAX_TOKENS` | `2048` | Max response length. |
| `TEMPERATURE` | `0.7` | Response creativity. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL. |
| `BRAVE_API_KEY` | _(empty)_ | Optional Brave Search key. |

---

## 🏗️ Project structure

```
ai-assistant-unlimited/
├── app.py                 # Flask server & API routes
├── assistant.py           # AI logic: Ollama calls, web search, version checks
├── builder.py             # Turns AI output into files, live preview, ZIP export
├── config.py              # Settings & environment variables
├── templates/
│   └── index.html         # Two-pane chat + workspace UI
├── start_production.sh     # Production startup (Ollama + web server)
├── requirements.txt
└── README.md
```

---

## 🔌 Tech stack

- **Backend:** Python · Flask · Gunicorn
- **AI:** Ollama (local LLMs — Qwen2.5-Coder)
- **Frontend:** Vanilla HTML/CSS/JS (no build step)
- **Search:** DuckDuckGo / Brave

---

## ⚠️ Honest expectations

This is a genuinely useful tool, but please know:

- It runs **open-source models**, which are great for help and drafts but **can make
  mistakes** — always review generated code.
- It is **not self-learning** — model knowledge is fixed at its training date. Web search
  adds current facts, and you can `ollama pull` newer models over time.
- It does **not self-heal** — if something breaks, just restart it.

---

## 📜 License

Released under the [MIT License](LICENSE) — free to use, modify, and share.

---

<div align="center">

**Made with 🍃 by MangliJuliano**

⭐ If you find this useful, give it a star!

</div>
