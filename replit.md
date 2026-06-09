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
- **Run button** (green ▶, top right, or press **F5** / Ctrl+Enter) — runs the file you
  have open. HTML/SVG opens in the live **Preview**; Python, Node, Bun/TypeScript, Bash,
  C/C++ and more run in the built-in **Terminal** and show their output. If a language's
  tool isn't installed yet, install it once in the Terminal and Run again.
- **ZIP button** (top right) — download your built project as a folder you can keep or run
  anywhere.
- **New button** — start a fresh project (clears the chat and files).
- **Model dropdown** (top right) — switch between installed AI models.

### Workspace tools (right side)

- **Explorer** (file icon) — your project files. The toolbar buttons let you **create a
  file**, **create a folder**, and **refresh**. Hover any file to **rename** or **delete**
  it. Everything here is yours to manage by hand — no AI required.
- **Preview** (eye icon) — the live, running version of your built app.
- **Terminal** (`>_` icon, or press **Ctrl+`**) — a real command line that runs *inside*
  your project folder. You can run `node`, `npm`, `python`, install packages, etc. Drag the
  top edge to resize it.
- **Settings** (gear, bottom-left of the workspace) — see "Make it yours" below.

### Make it yours (Settings)

Open the gear icon to customize nearly every detail of the editor and terminal: color
**theme** and **accent color**, font family and size, **line height**, **tab size**,
cursor **style** and **blink**, line numbers, whitespace marks, font **ligatures**, sticky
scroll, smooth scrolling, bracket-pair colors, indent guides, **format-on-save**, word wrap,
minimap, and the terminal's own font size and cursor. A **Reset** button puts everything
back to defaults. All choices are saved in your browser and applied instantly.

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
  (turns AI output into project files, live preview, ZIP export, rename + new folder) +
  `terminal.py` (opens a real shell via a pseudo-terminal/PTY).
- **Terminal:** `app.py` runs `flask-sock`; the browser's **xterm.js** connects to
  `/ws/terminal` over a WebSocket, which is wired to a PTY-backed shell running in your
  project folder. `nodejs-20` is installed so `node`/`npm`/`npx` work there. The Flask dev
  server runs `threaded=True` so the WebSocket and normal pages work at once.
- **Frontend:** `templates/index.html` (markup) + `static/styles.css` + `static/app.js` —
  two-pane chat + a VS Code-style workspace. The code editor is **Monaco** (the same
  engine VS Code uses), loaded from a CDN, with file tabs, an explorer (create/rename/
  delete files, create folders), syntax highlighting, a status bar, Ctrl+S to save, a
  built-in terminal (Ctrl+`), and a deep settings panel. Chats are remembered in your
  browser between visits.
- **Command Palette & shortcuts (VS Code-style):** press **F1** (or **Ctrl+Shift+P**) for
  the Command Palette — fuzzy-search every action (files, views, terminal, themes, editor
  commands). Press **Ctrl+P** for **Quick Open** (jump to any file by name). A full
  keyboard-shortcut layer works app-wide (Ctrl+S save, Ctrl+B sidebar, Ctrl+Shift+E
  explorer, Ctrl+, settings, Ctrl+Alt+N new file, Ctrl+` terminal, Alt+Z word wrap), plus
  a **Keyboard Shortcuts** reference (Settings → "See all keyboard shortcuts", or the
  Help command). Inside the editor, all of Monaco's own shortcuts (find, replace, multi-
  cursor, comment, format) work too. The "Commands" button in the status bar opens the
  palette. Global keys use a capture-phase handler so they win over Monaco where intended;
  when an overlay is open it traps navigation keys (arrows/Enter/Esc) regardless of focus.
- **Live preview safety:** the preview runs your generated app inside a sandboxed frame
  so its code can't read your chat history or touch your files. Apps that use browser
  storage still work — the server quietly provides an in-memory stand-in.
- **Terminal safety:** the terminal is a *real* shell on the server. It is **open when you
  run locally** (Option B). On the **published site** it is **OFF by default** — set a
  `TERMINAL_PASSWORD` secret to turn it on, and it will ask for that password before
  connecting. The server also refuses cross-site WebSocket connections (only the app's own
  pages can open the terminal), and fails closed: if a deployment is detected, the terminal
  stays locked unless a password is set.
- **Local model:** `qwen2.5-coder:3b` (fits the workspace's memory).
- **Deployed model:** `qwen2.5-coder:7b` via `start_production.sh` on a Reserved VM
  (it also sets `APP_ENV=production`, which locks the terminal unless a password is set).
- **AI engine:** Ollama, installed through `replit.nix`.

---

## User preferences

- Wants the app to stay free and private wherever possible.
- Prefers plain, non-technical explanations.
- Wants to be able to run and use the app independently without step-by-step help.
