# ─────────────────────────────────────────────────────────────────────────────
#  VIKA — Local Setup Script  (Windows PowerShell)
#  Installs Ollama, pulls the AI model, and starts VIKA in your browser.
#  Run: .\setup.ps1   (right-click → Run with PowerShell, or open PowerShell here)
# ─────────────────────────────────────────────────────────────────────────────
$ErrorActionPreference = "Stop"

$MODEL      = if ($env:DEFAULT_MODEL) { $env:DEFAULT_MODEL } else { "qwen2.5-coder:7b" }
$VIKA_PORT  = if ($env:VIKA_PORT)     { $env:VIKA_PORT }     else { "8080" }

Write-Host ""
Write-Host "  ██╗   ██╗██╗██╗  ██╗ █████╗ " -ForegroundColor Cyan
Write-Host "  ╚██╗ ██╔╝██║██║ ██╔╝██╔══██╗" -ForegroundColor Cyan
Write-Host "   ╚████╔╝ ██║█████╔╝ ███████║" -ForegroundColor Cyan
Write-Host "    ╚═══╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝" -ForegroundColor Cyan
Write-Host "  Versatile Intelligent Knowledge Assistant"
Write-Host "  Local Setup  |  Model: $MODEL  |  Port: $VIKA_PORT"
Write-Host ""

# ── 1. Python ────────────────────────────────────────────────────────────────
Write-Host "▶ Checking Python..." -ForegroundColor Cyan
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $python) {
  Write-Host "✗ Python 3.9+ is required." -ForegroundColor Red
  Write-Host "  Download it from https://python.org (check 'Add to PATH' during install)."
  exit 1
}
$pyver = & $python.Source -c "import sys; print(sys.version_info.major * 10 + sys.version_info.minor)"
if ([int]$pyver -lt 39) {
  Write-Host "✗ Python 3.9+ required." -ForegroundColor Red; exit 1
}
Write-Host "✓ Python OK: $(& $python.Source --version)" -ForegroundColor Green

# ── 2. pip dependencies ──────────────────────────────────────────────────────
Write-Host "`n▶ Installing Python dependencies..." -ForegroundColor Cyan
& $python.Source -m pip install --quiet --upgrade pip
& $python.Source -m pip install --quiet -r requirements.txt
Write-Host "✓ Dependencies installed." -ForegroundColor Green

# ── 3. Ollama ────────────────────────────────────────────────────────────────
Write-Host "`n▶ Checking Ollama..." -ForegroundColor Cyan
$ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollamaCmd) {
  Write-Host "  Downloading Ollama installer..." -ForegroundColor Yellow
  $installer = "$env:TEMP\OllamaSetup.exe"
  Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile $installer
  Start-Process -FilePath $installer -Wait
  # Refresh PATH
  $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
              [System.Environment]::GetEnvironmentVariable("PATH", "User")
  $ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
  if (-not $ollamaCmd) {
    Write-Host "✗ Ollama installation may need a terminal restart. Please reopen PowerShell and run this script again." -ForegroundColor Red
    exit 1
  }
}
Write-Host "✓ Ollama found." -ForegroundColor Green

# ── 4. Start Ollama daemon ───────────────────────────────────────────────────
Write-Host "`n▶ Starting Ollama service..." -ForegroundColor Cyan
try { Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 | Out-Null }
catch {
  Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
  Write-Host "  Waiting for Ollama..."
  for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep 1
    try { Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 1 | Out-Null; break } catch {}
  }
}
Write-Host "✓ Ollama is running." -ForegroundColor Green

# ── 5. Pull model ────────────────────────────────────────────────────────────
Write-Host "`n▶ Pulling AI model '$MODEL' (first run may take a few minutes)..." -ForegroundColor Cyan
ollama pull $MODEL
Write-Host "✓ Model ready." -ForegroundColor Green

# ── 6. Start VIKA ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "▶ Starting VIKA..." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Open your browser: http://localhost:$VIKA_PORT" -ForegroundColor Green
Write-Host "  To stop: press Ctrl+C"
Write-Host ""

$env:DEFAULT_MODEL = $MODEL
$env:VIKA_PORT     = $VIKA_PORT
& $python.Source app.py
