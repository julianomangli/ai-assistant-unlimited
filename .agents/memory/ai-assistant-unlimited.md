---
name: AI Assistant Unlimited
description: Architecture, constraints, and decisions for the local Flask+Ollama AI assistant with an in-app web-app builder.
---

# AI Assistant Unlimited

A free, local Flask web app using Ollama as the AI backend, plus an in-app builder
that generates static web apps from chat, shows a live preview, and exports a ZIP.

## Hard environment constraints (the dominant design force)
- Dev WORKSPACE RAM is ~7.7GB (≈4GB free) with 4 CPU — this is the cgroup limit and is
  what Ollama actually runs against while building. Disk is now plentiful (~31GB on the
  /home/runner overlay where ~/.ollama lives; was 5GB earlier).
- DEV vs DEPLOY trap: a user may say "I have 32GB RAM / 8 CPU" — that is the DEPLOYMENT
  (Reserved VM) machine, NOT the workspace. `free -h` in the workspace is authoritative
  and still showed 7.7GB. To use a big model in production you must run Ollama *inside*
  the deployment (Reserved VM + startup pull), since autoscale gunicorn has no Ollama.
- 7B models (~4.4-4.7GB) OOM in the 7.7GB workspace ("model requires more system memory"
  — mistral failed this way). Largest reliable local coder here is a 3B.
- Default model is `qwen2.5-coder:3b` — strong purpose-built coding model, ~4.5s replies,
  peaks ~5.7GB RAM used / 2.1GB free. Big jump over the old `tinyllama:latest` fallback.
- Frontier-quality (GPT-4/Claude class) models still cannot run locally — need GPUs.
- Ollama models do NOT persist across container restarts (re-pull needed).
- Ollama model names must include a tag (e.g. `:3b`, `:latest`) or `/api/chat` returns 404.

## User direction (decided)
**Why:** User asked for "best AI, free, local, under 5GB, never mistakes" — internally
contradictory. After being shown the tradeoffs they chose to **keep the tiny local model
(100% free + private)** and invest effort in the **builder UI** instead. Two better paths
remain if they change their mind: free hosted (Groq Llama-3.3-70B, needs free API key) or
paid frontier via Replit. No model is ever "never mistakes."

## Production deployment (Ollama in the deployed app)
**Why:** To use a big model (7B/14B) the deployment must run Ollama itself — autoscale
gunicorn has no Ollama, and the workspace caps at 8GB. A Reserved VM (32GB/8CPU) hosts it.
**How:** `.replit` deployment target is `vm`, run = `["bash", "start_production.sh"]`.
- `start_production.sh` exports `DEFAULT_MODEL` (default `qwen2.5-coder:7b`), starts
  `ollama serve`, pulls the model IN THE BACKGROUND, and `exec`s gunicorn immediately so
  the port binds and the health check passes during the (one-time per deploy) model download.
- gunicorn runs `--workers=1 --threads=8 --timeout=600`: ONE worker keeps in-memory
  session/conversation state consistent; long timeout covers slow CPU inference; threads
  give concurrency. Do not bump workers without moving session state off-process.
- `config.py` reads `DEFAULT_MODEL` from env, so dev stays `qwen2.5-coder:3b` (workflow
  runs `python app.py` with no env) while prod uses 7b via the script's export.
- Ollama models don't persist across deploys → re-pulled each deploy (background, so deploy
  still succeeds). `_ensure_ready()` in app.py returns friendly 503 "model downloading"
  messages while the pull is in flight.
- Ollama is provided by `replit.nix` (`pkgs.ollama`), so the binary is present in deploys.

## Builder architecture
- `builder.py` — parses AI output into files, writes to `generated_project/` (gitignored),
  lists/reads/saves files, zips, clears. Parse format the model is told to emit:
  `FILE: path` then a fenced code block. Falls back to bare fenced blocks with guessed names.
- `BUILDER_SYSTEM_PROMPT` in `assistant.py`; builder uses a separate AIAssistant with
  web search OFF and higher max_tokens (4096) for full-file output.
- Routes in `app.py`: `/api/build`, `/api/project/files`, `/api/project/file` (GET/POST),
  `/api/project/clear`, `/api/project/download` (zip), `/preview/<path>` (static, no-store).
- Builder files are GLOBAL (single `generated_project/`), not per-session — fine for a
  single-user local app; `/api/project/clear` wipes everything.

## Security lesson (caught in review)
- **Any AI/model-derived string rendered in the DOM must use `textContent`, never
  `innerHTML`.** Generated filenames were XSS-injectable via the file tree. Defense in
  depth: `sanitize_path()` also restricts filename chars to `[A-Za-z0-9._-]` and strips
  `..`/leading dots. Preview serving uses `send_from_directory` (traversal-safe).

## Gotcha
- Flask caches templates — restart the "Start application" workflow after editing
  `templates/index.html` or changes won't show.
