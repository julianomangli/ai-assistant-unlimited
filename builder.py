import os
import re
import io
import zipfile
import shutil

PROJECT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_project")

_LANG_FILENAMES = {
    "html": "index.html",
    "css": "style.css",
    "javascript": "script.js",
    "js": "script.js",
    "jsx": "app.jsx",
    "ts": "script.ts",
    "typescript": "script.ts",
    "python": "main.py",
    "py": "main.py",
    "json": "data.json",
    "md": "README.md",
    "markdown": "README.md",
}


def ensure_project_dir():
    os.makedirs(PROJECT_DIR, exist_ok=True)


_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]")


def sanitize_path(path: str) -> str:
    path = path.replace("\\", "/").strip().strip("`").strip().lstrip("/")
    parts = []
    for p in path.split("/"):
        if p in ("", ".", ".."):
            continue
        cleaned = _SAFE_CHARS.sub("_", p).lstrip(".") or "file"
        parts.append(cleaned)
    return "/".join(parts) if parts else "file.txt"


def _guess_filename(lang: str, content: str, existing: dict) -> str:
    lang = (lang or "").lower()
    base = _LANG_FILENAMES.get(lang)
    if not base:
        lowered = content.lower()
        if "<!doctype" in lowered or "<html" in lowered:
            base = "index.html"
        else:
            base = f"file{len(existing) + 1}.txt"
    name = base
    i = 1
    while name in existing:
        stem, ext = os.path.splitext(base)
        name = f"{stem}_{i}{ext}"
        i += 1
    return name


def parse_files(text: str) -> dict:
    """Extract {path: content} from an AI response."""
    files: dict = {}

    # Primary format:  FILE: path\n```lang\n...content...\n```
    pattern = re.compile(
        r"FILE:\s*([^\n`]+?)\s*\n```[^\n]*\n(.*?)```",
        re.DOTALL,
    )
    for m in pattern.finditer(text):
        path = sanitize_path(m.group(1))
        files[path] = m.group(2).rstrip("\n") + "\n"

    # Fallback: bare fenced code blocks
    if not files:
        for lang, content in re.findall(r"```(\w*)\n(.*?)```", text, re.DOTALL):
            name = _guess_filename(lang, content, files)
            files[name] = content.rstrip("\n") + "\n"

    return files


def strip_code(text: str) -> str:
    """Remove FILE blocks / code fences, leaving the prose explanation."""
    text = re.sub(r"FILE:\s*[^\n`]+?\s*\n```[^\n]*\n.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"```\w*\n.*?```", "", text, flags=re.DOTALL)
    cleaned = "\n".join(line for line in text.splitlines() if line.strip())
    return cleaned.strip()


def write_files(files: dict) -> list:
    ensure_project_dir()
    written = []
    for path, content in files.items():
        safe = sanitize_path(path)
        full = os.path.join(PROJECT_DIR, safe)
        os.makedirs(os.path.dirname(full) or PROJECT_DIR, exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(safe)
    return written


def list_files() -> list:
    ensure_project_dir()
    out = []
    for root, _dirs, filenames in os.walk(PROJECT_DIR):
        for fn in filenames:
            rel = os.path.relpath(os.path.join(root, fn), PROJECT_DIR)
            out.append(rel.replace("\\", "/"))
    return sorted(out)


def read_file(path: str):
    safe = sanitize_path(path)
    full = os.path.join(PROJECT_DIR, safe)
    if os.path.isfile(full):
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    return None


def save_file(path: str, content: str):
    safe = sanitize_path(path)
    full = os.path.join(PROJECT_DIR, safe)
    os.makedirs(os.path.dirname(full) or PROJECT_DIR, exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def clear_project():
    if os.path.isdir(PROJECT_DIR):
        shutil.rmtree(PROJECT_DIR)
    ensure_project_dir()


def has_index() -> bool:
    return os.path.isfile(os.path.join(PROJECT_DIR, "index.html"))


def make_zip() -> io.BytesIO:
    ensure_project_dir()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, filenames in os.walk(PROJECT_DIR):
            for fn in filenames:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, PROJECT_DIR)
                zf.write(full, rel)
    buf.seek(0)
    return buf
