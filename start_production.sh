#!/usr/bin/env bash
# Production startup for the Reserved VM deployment.
# Runs the Ollama server + a larger coding model alongside the Flask app.
set -u

# Bigger model for the 32GB/8CPU VM. Override by setting DEFAULT_MODEL in deployment secrets.
export DEFAULT_MODEL="${DEFAULT_MODEL:-qwen2.5-coder:7b}"
export OLLAMA_HOST="127.0.0.1:11434"

# Marks this as the public deployment. The in-app terminal stays OFF here unless a
# TERMINAL_PASSWORD secret is set (otherwise it would hand a shell to any visitor).
export APP_ENV="production"

echo "[startup] Launching Ollama server..."
ollama serve &

# Wait for Ollama, then pull the model in the background so the web server can
# bind its port immediately and pass the deployment health check.
(
  for i in $(seq 1 180); do
    if curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
      echo "[startup] Ollama ready. Pulling model: $DEFAULT_MODEL"
      ollama pull "$DEFAULT_MODEL" && echo "[startup] Model ready: $DEFAULT_MODEL"
      break
    fi
    sleep 1
  done
) &

echo "[startup] Starting web server on :5000 (model downloads in background)..."
exec gunicorn --bind=0.0.0.0:5000 --reuse-port --workers=1 --threads=8 --timeout=600 app:app
