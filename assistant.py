import requests
import json
import re
import time
from datetime import datetime, timezone
from config import (
    ENABLE_WEB_SEARCH, ENABLE_VERSION_CHECK, BRAVE_API_KEY,
    DEFAULT_MODEL, MAX_TOKENS, TEMPERATURE, OLLAMA_BASE_URL
)

WEB_SEARCH_TRIGGERS = [
    "latest", "newest", "current", "today", "recently", "what's new",
    "update", "release", "how to", "documentation", "error", "issue",
    "new in", "version of", "tutorial"
]


def _should_search(message: str) -> bool:
    msg_lower = message.lower()
    return any(trigger in msg_lower for trigger in WEB_SEARCH_TRIGGERS)


def _duckduckgo_search(query: str, max_results: int = 3) -> list[dict]:
    try:
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_redirect": "1", "no_html": "1"}
        resp = requests.get(url, params=params, timeout=8)
        data = resp.json()
        results = []
        for item in data.get("RelatedTopics", [])[:max_results]:
            if "Text" in item and "FirstURL" in item:
                results.append({
                    "title": item["Text"][:100],
                    "url": item["FirstURL"],
                    "snippet": item["Text"]
                })
        return results
    except Exception:
        return []


def _brave_search(query: str, max_results: int = 3) -> list[dict]:
    try:
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": BRAVE_API_KEY,
        }
        params = {"q": query, "count": max_results}
        resp = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers, params=params, timeout=8
        )
        data = resp.json()
        results = []
        for item in data.get("web", {}).get("results", [])[:max_results]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("description", "")
            })
        return results
    except Exception:
        return []


def web_search(query: str, max_results: int = 3) -> list[dict]:
    if BRAVE_API_KEY:
        results = _brave_search(query, max_results)
        if results:
            return results
    return _duckduckgo_search(query, max_results)


def _check_pypi(package: str) -> dict | None:
    try:
        resp = requests.get(f"https://pypi.org/pypi/{package}/json", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            info = data.get("info", {})
            return {
                "package": package,
                "source": "PyPI",
                "version": info.get("version", "unknown"),
                "url": info.get("project_url", f"https://pypi.org/project/{package}/")
            }
    except Exception:
        pass
    return None


def _check_npm(package: str) -> dict | None:
    try:
        resp = requests.get(f"https://registry.npmjs.org/{package}/latest", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "package": package,
                "source": "NPM",
                "version": data.get("version", "unknown"),
                "url": f"https://www.npmjs.com/package/{package}"
            }
    except Exception:
        pass
    return None


def _check_github(repo: str) -> dict | None:
    try:
        resp = requests.get(
            f"https://api.github.com/repos/{repo}/releases/latest",
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "package": repo,
                "source": "GitHub",
                "version": data.get("tag_name", "unknown"),
                "url": data.get("html_url", f"https://github.com/{repo}/releases")
            }
    except Exception:
        pass
    return None


KNOWN_PACKAGES = {
    "pypi": ["flask", "django", "requests", "fastapi", "numpy", "pandas", "tensorflow", "pytorch"],
    "npm": ["react", "vue", "typescript", "next", "vercel", "express", "angular", "svelte"],
    "github": ["ollama/ollama", "vercel/vercel", "facebook/react"],
}


def check_versions(query: str) -> list[dict]:
    if not ENABLE_VERSION_CHECK:
        return []
    results = []
    query_lower = query.lower()
    for pkg in KNOWN_PACKAGES["pypi"]:
        if pkg in query_lower:
            info = _check_pypi(pkg)
            if info:
                results.append(info)
    for pkg in KNOWN_PACKAGES["npm"]:
        if pkg in query_lower:
            info = _check_npm(pkg)
            if info:
                results.append(info)
    for repo in KNOWN_PACKAGES["github"]:
        name = repo.split("/")[-1]
        if name in query_lower:
            info = _check_github(repo)
            if info:
                results.append(info)
    return results


def format_search_results(results: list[dict]) -> str:
    if not results:
        return ""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"📰 **Latest Search Results:**\n(Updated: {timestamp})\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. **{r['title']}**")
        lines.append(f"   🔗 {r['url']}")
        if r.get("snippet"):
            lines.append(f"   📝 {r['snippet'][:200]}")
        lines.append("")
    return "\n".join(lines)


def format_version_results(results: list[dict]) -> str:
    if not results:
        return ""
    lines = []
    for r in results:
        lines.append(f"🆕 **New Version Available:**")
        lines.append(f"   📦 Package: {r['package']}")
        lines.append(f"   📌 Latest Version: {r['version']}")
        lines.append(f"   📥 Source: {r['source']} — {r['url']}")
        lines.append("")
    return "\n".join(lines)


BUILDER_SYSTEM_PROMPT = """You are an expert full-stack web developer AI inside an app builder. \
When the user asks you to build, create, or change an app, you output complete, runnable web files.

OUTPUT FORMAT — follow it exactly. For every file you write, use:

FILE: index.html
```html
<full file content here>
```

Repeat the FILE block for each file you create or modify.

RULES:
- Prefer a SINGLE self-contained index.html with inline <style> and <script> so it previews instantly.
- Output COMPLETE files only — never partial snippets, never "..." or "rest of code here".
- Always include a full index.html as the entry point so the live preview works.
- Make the app visually polished, responsive, and actually functional.
- When the user asks for a change, re-output the full updated file(s).
- After the file blocks, add ONE short sentence describing what you built. No long explanations.
"""


class AIAssistant:
    def __init__(
        self,
        model: str = None,
        system_prompt: str = None,
        enable_web_search: bool = None
    ):
        self.model = model or DEFAULT_MODEL
        self.enable_web_search = enable_web_search if enable_web_search is not None else ENABLE_WEB_SEARCH
        self.conversation_history: list[dict] = []
        self.system_prompt = system_prompt or (
            "You are an expert AI coding assistant. You help with programming, "
            "software development, debugging, and technical questions. "
            "You provide clear, accurate, and up-to-date information. "
            "When web search results are provided, use them to give current information."
        )

    def _build_context(self, message: str) -> str:
        context_parts = []
        if self.enable_web_search and _should_search(message):
            search_results = web_search(message)
            if search_results:
                context_parts.append(format_search_results(search_results))
            version_results = check_versions(message)
            if version_results:
                context_parts.append(format_version_results(version_results))
        return "\n".join(context_parts)

    def _call_ollama(self, messages: list[dict], stream: bool = False, max_tokens: int = None):
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "num_predict": max_tokens or MAX_TOKENS,
                "temperature": TEMPERATURE
            }
        }
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            stream=stream,
            timeout=120
        )
        resp.raise_for_status()
        return resp

    def chat(self, message: str, max_tokens: int = None) -> str:
        context = self._build_context(message)
        user_content = message
        if context:
            user_content = f"{context}\n\nUser question: {message}"

        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": user_content})

        resp = self._call_ollama(messages, stream=False, max_tokens=max_tokens)
        data = resp.json()
        assistant_message = data["message"]["content"]

        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": assistant_message})

        return assistant_message

    def chat_stream(self, message: str):
        context = self._build_context(message)
        user_content = message
        if context:
            yield context + "\n\n---\n\n"
            user_content = f"{context}\n\nUser question: {message}"

        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": user_content})

        full_response = ""
        resp = self._call_ollama(messages, stream=True)
        for line in resp.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    chunk = data.get("message", {}).get("content", "")
                    if chunk:
                        full_response += chunk
                        yield chunk
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    pass

        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": full_response})

    def clear_history(self):
        self.conversation_history = []

    def get_available_models(self) -> list[str]:
        try:
            resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []

    def is_ollama_running(self) -> bool:
        try:
            resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False
