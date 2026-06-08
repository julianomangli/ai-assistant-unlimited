#!/usr/bin/env bash
# Production startup for the Reserved VM deployment.
# Model download is managed inside the Flask app (with live progress tracking)
# so the web server starts immediately and visitors see a real progress screen.
set -u

# Bigger model for the 32GB/8CPU VM. Override via DEFAULT_MODEL deployment secret.
export DEFAULT_MODEL="${DEFAULT_MODEL:-qwen2.5-coder:14b}"
export OLLAMA_HOST="127.0.0.1:11434"

# Store models OUTSIDE the project workspace so they survive re-deploys.
# /home/runner/.ollama_cache is never touched by the deployment sync.
export OLLAMA_MODELS="/home/runner/.ollama_cache"

# Marks this as the public deployment. Terminal stays OFF unless TERMINAL_PASSWORD is set.
export APP_ENV="production"

echo "[startup] Launching Ollama server (models at $OLLAMA_MODELS)..."
ollama serve &

echo "[startup] Starting web server — model pull is tracked inside the app..."
exec gunicorn --bind=0.0.0.0:5000 --reuse-port --workers=1 --threads=8 --timeout=600 app:app
