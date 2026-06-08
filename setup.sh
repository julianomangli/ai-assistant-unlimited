#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
#  VIKA — Local Setup Script  (Linux & macOS)
#  Installs Ollama, pulls the AI model, and starts VIKA in your browser.
#  Run: bash setup.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

VIKA_PORT="${VIKA_PORT:-8080}"
MODEL="${DEFAULT_MODEL:-qwen2.5-coder:7b}"

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

step()  { echo -e "\n${CYAN}${BOLD}▶ $*${NC}"; }
ok()    { echo -e "${GREEN}✓ $*${NC}"; }
warn()  { echo -e "${YELLOW}⚠ $*${NC}"; }
fail()  { echo -e "${RED}✗ $*${NC}"; exit 1; }

echo ""
echo -e "${BOLD}  ██╗   ██╗██╗██╗  ██╗ █████╗ ${NC}"
echo -e "${BOLD}  ╚██╗ ██╔╝██║██║ ██╔╝██╔══██╗${NC}"
echo -e "${BOLD}   ╚████╔╝ ██║█████╔╝ ███████║${NC}"
echo -e "${BOLD}    ╚═══╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝${NC}"
echo -e "  Versatile Intelligent Knowledge Assistant"
echo -e "  Local Setup  •  Model: ${CYAN}$MODEL${NC}  •  Port: ${CYAN}$VIKA_PORT${NC}"
echo ""

# ── 1. Python ────────────────────────────────────────────────────────────────
step "Checking Python..."
PYTHON=$(command -v python3 || command -v python || "")
if [ -z "$PYTHON" ]; then
  fail "Python 3.9+ is required. Install it from https://python.org and rerun this script."
fi
PY_VER=$($PYTHON -c "import sys; print(sys.version_info.major*10+sys.version_info.minor)")
if [ "$PY_VER" -lt 39 ]; then
  fail "Python 3.9+ required (found $($PYTHON --version))."
fi
ok "Python found: $($PYTHON --version)"

# ── 2. pip dependencies ──────────────────────────────────────────────────────
step "Installing Python dependencies..."
$PYTHON -m pip install --quiet --upgrade pip
$PYTHON -m pip install --quiet -r requirements.txt
ok "Dependencies installed."

# ── 3. Ollama ────────────────────────────────────────────────────────────────
step "Checking Ollama..."
if command -v ollama > /dev/null 2>&1; then
  ok "Ollama already installed: $(ollama --version 2>&1 | head -1)"
else
  echo "  Installing Ollama..."
  OS=$(uname -s)
  if [ "$OS" = "Darwin" ]; then
    if command -v brew > /dev/null 2>&1; then
      brew install ollama
    else
      warn "Homebrew not found. Downloading Ollama installer..."
      curl -fsSL https://ollama.com/install.sh | sh
    fi
  elif [ "$OS" = "Linux" ]; then
    curl -fsSL https://ollama.com/install.sh | sh
  else
    fail "Unsupported OS: $OS. Install Ollama manually from https://ollama.com then rerun."
  fi
  ok "Ollama installed."
fi

# ── 4. Start Ollama daemon (if not running) ──────────────────────────────────
step "Starting Ollama service..."
if ! curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
  nohup ollama serve > /tmp/ollama.log 2>&1 &
  OLLAMA_PID=$!
  echo "  Waiting for Ollama to start (pid $OLLAMA_PID)..."
  for i in $(seq 1 30); do
    curl -sf http://localhost:11434/api/tags > /dev/null 2>&1 && break
    sleep 1
  done
fi
curl -sf http://localhost:11434/api/tags > /dev/null 2>&1 || fail "Ollama did not start. Check /tmp/ollama.log"
ok "Ollama is running."

# ── 5. Pull model ────────────────────────────────────────────────────────────
step "Pulling AI model '$MODEL' (this may take a few minutes the first time)..."
ollama pull "$MODEL"
ok "Model ready."

# ── 6. Start VIKA ────────────────────────────────────────────────────────────
step "Starting VIKA..."
echo ""
echo -e "  ${BOLD}Open your browser: ${CYAN}http://localhost:$VIKA_PORT${NC}"
echo ""
echo "  To stop: press Ctrl+C"
echo "  To change model: DEFAULT_MODEL=qwen2.5-coder:14b bash setup.sh"
echo ""

VIKA_PORT=$VIKA_PORT DEFAULT_MODEL=$MODEL $PYTHON app.py
