<div align="center">

# ✦ VIKA — AI-Powered Dev Studio

### Free · Private · Runs 100% on your own machine

Chat with a local AI, **describe an app in plain English**, watch it build in a
**live preview**, edit the files, and **download it as a ZIP** — all running on your
device with no accounts, no cloud, no fees.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-web%20app-000000?logo=flask&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-local%20AI-000000?logo=ollama&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e)
![Privacy](https://img.shields.io/badge/Privacy-100%25%20local-7c6cff)

**Made with 🍃 by MangliJuliano**

</div>

---

## 🚀 Run on your own machine — three ways

Pick whichever fits. **No accounts required for any of them.**

---

### Option A — One command with Docker (easiest, works on any OS)

> Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) (free).

```bash
git clone https://github.com/julianomangli/ai-assistant-unlimited.git
cd ai-assistant-unlimited
docker compose up
```

Open **http://localhost:8080** — that's it. Ollama and the AI model download automatically on first run.

**Change the model** — edit `docker-compose.yml` → `DEFAULT_MODEL` (see model table below), then `docker compose up`.

---

### Option B — Automated setup script (no Docker)

**macOS / Linux:**
```bash
git clone https://github.com/julianomangli/ai-assistant-unlimited.git
cd ai-assistant-unlimited
bash setup.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/julianomangli/ai-assistant-unlimited.git
cd ai-assistant-unlimited
.\setup.ps1
```

The script installs Ollama if you don't have it, pulls the model, installs Python deps, and opens VIKA at **http://localhost:8080**.

---

### Option C — Manual setup (full control)

#### 1. Prerequisites
- [Python 3.9+](https://www.python.org/)
- [Ollama](https://ollama.com/) installed

#### 2. Clone & install
```bash
git clone https://github.com/julianomangli/ai-assistant-unlimited.git
cd ai-assistant-unlimited
pip install -r requirements.txt
```

#### 3. Pull a model
```bash
# Fast, works on 8 GB RAM
ollama pull qwen2.5-coder:7b

# Lighter, works on 4 GB RAM
ollama pull qwen2.5-coder:3b

# Best quality, needs 16 GB+ RAM
ollama pull qwen2.5-coder:14b
```

#### 4. Start
```bash
# Terminal 1 — AI engine
ollama serve

# Terminal 2 — VIKA
python app.py
```

Open **http://localhost:5000** 🎉

---

## 🧠 How to use VIKA

| Mode | What it does |
|------|-------------|
| **Chat** | Ask anything — code help, explanations, debugging, any question |
| **Build** | Describe an app ("build a to-do list with dark UI") — VIKA writes it live |
| **Preview tab** | See your generated app render in real time |
| **Code tab** | Browse and edit generated files with Monaco editor |
| **ZIP button** | Download the whole project as a folder you can run anywhere |
| **New button** | Start a fresh project |
| **Model dropdown** | Switch between all installed Ollama models |
| **Terminal (>_ )** | Real shell inside your project folder — run node, npm, python, anything |
| **Settings (gear)** | Customise editor theme, font, colours, behaviour |

---

## 🤖 Recommended models

| Model | RAM needed | Speed | Quality | Command |
|-------|-----------|-------|---------|---------|
| `qwen2.5-coder:3b` | 4 GB | ⚡⚡⚡ Fast | Good | `ollama pull qwen2.5-coder:3b` |
| `qwen2.5-coder:7b` | 8 GB | ⚡⚡ Medium | Great | `ollama pull qwen2.5-coder:7b` |
| `qwen2.5-coder:14b` | 16 GB | ⚡ Slower | Excellent | `ollama pull qwen2.5-coder:14b` |
| `llama3.2:3b` | 4 GB | ⚡⚡⚡ Fast | Good | `ollama pull llama3.2:3b` |
| `mistral:7b` | 8 GB | ⚡⚡ Medium | Great | `ollama pull mistral:7b` |

Any model on [ollama.com/search](https://ollama.com/search) works — just pull it and select it from the dropdown.

---

## ⚙️ Configuration (all optional)

Set these as environment variables or edit `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_MODEL` | `qwen2.5-coder:7b` | Ollama model to load |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server address |
| `VIKA_PORT` | `5000` | Port the web app listens on |
| `ENABLE_WEB_SEARCH` | `True` | Real-time web search for current info |
| `MAX_TOKENS` | `4096` | Max response length |
| `TEMPERATURE` | `0.75` | Response creativity (0 = precise, 1 = creative) |
| `APP_PASSWORD` | _(empty)_ | Protect the app with a password |
| `TERMINAL_PASSWORD` | _(empty)_ | Enable terminal on published/remote deployments |
| `BRAVE_API_KEY` | _(empty)_ | Optional Brave Search API key for better search |

---

## 🏗️ Project structure

```
ai-assistant-unlimited/
├── app.py              # Flask server & all API routes
├── assistant.py        # AI logic: Ollama calls, web search, version checks
├── builder.py          # Turns AI output into files, live preview, ZIP export
├── knowledge.py        # Three-tier speed system: instant cache + learned Q&A
├── terminal.py         # WebSocket-backed real terminal (xterm.js + PTY)
├── config.py           # Settings & environment variables
├── templates/
│   └── index.html      # Full IDE UI (Monaco editor, file explorer, preview)
├── static/
│   ├── app.js          # Frontend: streaming chat, file cards, workspace
│   └── styles.css      # UI styles
├── docker-compose.yml  # One-command Docker setup
├── Dockerfile          # VIKA container image
├── setup.sh            # Automated installer (Linux/macOS)
├── setup.ps1           # Automated installer (Windows PowerShell)
├── start_production.sh # Production startup (Ollama + gunicorn)
└── requirements.txt
```

---

## 🔌 Tech stack

- **Backend:** Python · Flask · flask-sock (WebSockets)
- **AI:** Ollama (local LLMs — any model)
- **Editor:** Monaco (same engine as VS Code)
- **Terminal:** xterm.js + PTY
- **Search:** DuckDuckGo / Brave
- **Frontend:** Vanilla HTML/CSS/JS (zero build step)

---

## ⚠️ Honest expectations

- Runs **open-source models** — great for help and drafts, but **can make mistakes**. Always review generated code.
- **Not self-learning** — model knowledge is fixed at its training date. Web search adds current facts. Pull newer models with `ollama pull`.
- **Completely private** — nothing leaves your machine. No telemetry, no cloud calls.
- **Not self-healing** — if something crashes, just rerun the start command.

---

## 📜 License

Released under the [MIT License](LICENSE) — free to use, modify, and share.

---

<div align="center">

**Made with 🍃 by MangliJuliano**

⭐ If you find this useful, give it a star!

</div>
