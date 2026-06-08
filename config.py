import os

ENABLE_WEB_SEARCH = os.environ.get("ENABLE_WEB_SEARCH", "True").lower() == "true"
ENABLE_VERSION_CHECK = os.environ.get("ENABLE_VERSION_CHECK", "True").lower() == "true"
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "qwen2.5-coder:3b")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "4096"))
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.75"))
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
