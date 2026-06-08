#!/bin/bash
# VIKA Docker entrypoint
# Waits for Ollama, pulls the model if needed, then starts the web app.
set -e

OLLAMA_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
MODEL="${DEFAULT_MODEL:-qwen2.5-coder:7b}"

echo ""
echo "  ██╗   ██╗██╗██╗  ██╗ █████╗ "
echo "  ██║   ██║██║██║ ██╔╝██╔══██╗"
echo "  ██║   ██║██║█████╔╝ ███████║"
echo "  ╚██╗ ██╔╝██║██╔═██╗ ██╔══██║"
echo "   ╚████╔╝ ██║██║  ██╗██║  ██║"
echo "    ╚═══╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝"
echo "  Versatile Intelligent Knowledge Assistant"
echo ""
echo "  Ollama  : $OLLAMA_URL"
echo "  Model   : $MODEL"
echo ""

# Wait for Ollama to be reachable
echo "⏳ Waiting for Ollama to start..."
until curl -sf "$OLLAMA_URL/api/tags" > /dev/null 2>&1; do
  sleep 2
done
echo "✅ Ollama is ready."

# Pull the model (fast no-op if already cached)
echo "📦 Checking model '$MODEL'..."
curl -sf -X POST "$OLLAMA_URL/api/pull" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$MODEL\",\"stream\":false}" \
  --max-time 600 \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ' + d.get('status','done'))" 2>/dev/null || true
echo "✅ Model ready."

echo ""
echo "🚀 Starting VIKA at http://localhost:8080"
echo ""

exec python app.py
