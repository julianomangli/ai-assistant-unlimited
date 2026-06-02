# AI Assistant Unlimited

A free, private, local AI assistant with a built-in **app builder** — describe an app
in plain English and watch it appear in a live preview, edit the files, and download
the whole thing as a ZIP. The AI runs on **Ollama** (no external accounts, your data
stays on the machine), with optional real-time web search for current info.

---

## ▶️ How to run it yourself (no need to ask anyone)

You have **two ways** to use this app. Pick whichever fits.

### Option A — The published website (always on, easiest)
1. Open your browser and go to your live address: **https://ai-assistant-unlimited.replit.app**
2. That's it — start chatting or switch to **Build** mode.

- Use this when you want it available 24/7 from any device without opening Replit.
- **Important:** every time you change the project you must click **Publish** again for
  the live site to update.
- After each publish, the AI model downloads for a few minutes. During that window the
  app will say "model is downloading — try again shortly." That's normal; just wait.
- The always-on server costs a **flat monthly fee** (it's a reserved machine). No
  per-message charges.

### Option B — Inside Replit (free, runs while the project is open)
1. Open this project on Replit.
2. Click the green **Run** button at the top.
3. Wait until the preview window on the right shows the app (about 10–20 seconds).
4. Use it. When you close the project, it stops (free, nothing running in the background).

- Use this when you just want to use or improve it for free and don't need it online 24/7.

---

## 🧠 How to use the app

- **Chat mode** — ask coding questions, get explanations, debug help.
- **Build mode** — describe an app ("build a calculator", "make a to-do list"). The AI
  writes the code, it appears in the **Preview** tab on the right, and the files show up
  in the **Code** tab where you can view/edit them.
- **ZIP button** (top right) — download your built project as a folder you can keep or run
  anywhere.
- **New button** — start a fresh project (clears the chat and files).
- **Model dropdown** (top right) — switch between installed AI models.

---

## ✅ What this app really is (honest expectations)

It's genuinely useful, but please read this so nothing surprises you:

- **Free to run locally** in Replit (Option B). The always-on website (Option A) costs a
  flat monthly machine fee.
- **Private** — the AI runs on your machine; your chats aren't sent to OpenAI/Anthropic.
- **It is NOT self-learning.** It does not remember or get smarter from how you use it.
  Each model has fixed knowledge from when it was trained.
- **It DOES make mistakes.** It's a small/medium open model — great for help and drafts,
  but always review its code. No AI is "never wrong."
- **It does NOT fix itself or guarantee never crashing.** If something breaks, you (or I)
  restart it. The Run button restarts everything cleanly.
- **"Up to date" has limits.** Web search gives it current facts for questions, but the
  model's built-in knowledge is frozen at its training date. To get newer/smarter models
  as technology evolves, you pull an updated model (see below).

---

## 🔄 Keeping it current as tech evolves

The AI model doesn't auto-update. To upgrade to a newer or bigger model later:

1. In the Replit Shell, run: `ollama pull <model-name>` (e.g. `ollama pull qwen2.5-coder:14b`).
2. Pick it from the model dropdown in the app, or set it as default.

Ask the assistant (me) any time to install or switch models for you.

---

## 🛠️ Technical overview (for reference)

- **Backend:** Flask (`app.py`) + `assistant.py` (Ollama calls, web search) + `builder.py`
  (turns AI output into project files, live preview, ZIP export).
- **Frontend:** `templates/index.html` — two-pane chat + workspace UI.
- **Local model:** `qwen2.5-coder:3b` (fits the workspace's memory).
- **Deployed model:** `qwen2.5-coder:7b` via `start_production.sh` on a Reserved VM.
- **AI engine:** Ollama, installed through `replit.nix`.

---

## User preferences

- Wants the app to stay free and private wherever possible.
- Prefers plain, non-technical explanations.
- Wants to be able to run and use the app independently without step-by-step help.
