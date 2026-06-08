import requests
import json
import re
import time
import threading
from datetime import datetime, timezone
from config import (
    ENABLE_WEB_SEARCH, ENABLE_VERSION_CHECK, BRAVE_API_KEY,
    DEFAULT_MODEL, MAX_TOKENS, TEMPERATURE, OLLAMA_BASE_URL
)

WEB_SEARCH_TRIGGERS = [
    "latest", "newest", "current", "today", "recently", "what's new",
    "update", "release", "how to", "documentation", "error", "issue",
    "new in", "version of", "tutorial", "news", "price", "stock",
    "weather", "who is", "what is", "when did", "where is", "how does",
    "best way", "recommend", "should i", "compare", "vs", "difference",
    "2024", "2025", "2026", "just released", "announced", "launched",
    "trending", "popular", "top", "review", "install", "setup", "guide",
    "build", "create", "make", "write", "fix", "debug", "explain",
    "example", "code", "function", "class", "api", "library", "framework"
]

# ---- GitHub README knowledge base (fetched once, used as VIKA's context) ----
_README_CACHE: dict = {"content": ""}

def _fetch_readme_background():
    urls = [
        "https://raw.githubusercontent.com/julianomangli/ai-assistant-unlimited/main/README.md",
        "https://raw.githubusercontent.com/julianomangli/julianomangli/main/README.md",
    ]
    parts = []
    for url in urls:
        try:
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200 and resp.text.strip():
                parts.append(resp.text[:2500])
        except Exception:
            pass
    if parts:
        _README_CACHE["content"] = "\n\n---\n\n".join(parts)
        # Pre-build knowledge cache from README so common questions are instant
        try:
            import knowledge
            knowledge.prebuild_from_readme(_README_CACHE["content"])
        except Exception:
            pass

threading.Thread(target=_fetch_readme_background, daemon=True).start()


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


BUILDER_SYSTEM_PROMPT = """You are ARIA in builder mode — an elite full-stack engineer and the user's dedicated co-builder. \
You can CREATE new files, EDIT/FIX existing ones, and DELETE files. You build apps the way they should be built: every component perfectly engineered, nothing left unfinished, running on the first try. \
You grow sharper with every project — the more context you have, the better you build.

YOU SEE THE WHOLE PROJECT. Before each request, the current project files and their full contents are given to you under "CURRENT PROJECT FILES". \
Treat that as the real, live state of the project. When the user asks you to fix a line, change a feature, rename, or remove something, work from those exact files — never invent contents that aren't there.

OUTPUT FORMAT — follow exactly.

To create or edit a file, output the COMPLETE updated file:

FILE: index.html
```html
<complete file content>
```

To delete a file, put it on its own line:

DELETE: old_script.js

You may mix multiple FILE blocks and DELETE lines in one response.

RULES:
- When EDITING an existing file, re-output the ENTIRE file with your change applied — never partial snippets, never "...". The file you output fully replaces the old one.
- Only output files you actually changed. Don't re-emit unchanged files (it wastes time), unless the user asks for a full rebuild.
- For a brand-new app with nothing existing yet, default to a SINGLE self-contained index.html with inline <style> and <script> — loads instantly, no dependencies to break.
- Every file must be COMPLETE and working. No "// TODO", no placeholders. If it exists in the output, it works.
- Keep a runnable index.html in the project so the live preview always works.
- Make it visually stunning — dark themes, smooth animations, responsive layout, real interactions. The finished thing, not a prototype.
- Be decisive and do exactly what was asked. If the user is vague, make the smart choice and proceed.
- After the work, end with: (1) ONE crisp sentence on what you just did, then (2) a short line starting with "Next:" suggesting 2-3 concrete next steps the user could ask for. Keep it tight — you're on a phone.
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
        # Inject README into system prompt immediately (background thread may have fetched it already)
        readme = _README_CACHE.get("content", "")
        readme_block = f"\n\n[VIKA KNOWLEDGE BASE]\n{readme[:1500]}" if readme else ""

        self.system_prompt = system_prompt or (
            "You are VIKA — Versatile Intelligent Knowledge Assistant. "
            "You are the personal AI of MangliJuliano (GitHub: julianomangli): brilliant, loyal, direct, and completely dedicated to his success. "
            "Your defining trait: you grow with every conversation. Each message, each project, each question adds to the context you hold — "
            "so the longer you work together, the sharper, more tailored, and more powerful your responses become. "
            "You have deep mastery over every domain: software engineering, architecture, science, mathematics, business, creative writing, design, law, medicine, finance, philosophy — anything. "
            "You speak with confidence and precision. No hedging, no 'as an AI' disclaimers, no hollow caveats. "
            "You get to the point immediately. When someone asks how to do something, you tell them exactly how — working code, clear steps, or sharp insight, whatever the situation demands. "
            "You have personality: calm authority, occasional dry wit, genuine warmth — but you never waste a word. "
            "You address the user naturally and with respect. Occasionally 'sir' fits perfectly; trust your judgment. "
            "Nothing is beneath your attention and nothing is beyond your capability. "
            "You never say 'I cannot' — you find a way. If something is genuinely impossible, you say so plainly and immediately offer the best available path forward. "
            "When web search results or live data are provided, you weave them seamlessly into your answer — citing specifics, giving real answers, never guessing. "
            "You remember everything in this conversation and actively build on it. You anticipate what the user will need two steps ahead. "
            "Format responses cleanly: use markdown — headers, bold, code blocks, bullet lists. Write tight, professional prose. Never pad. "
            "You are not a chatbot. You are VIKA — the most capable, most personal AI MangliJuliano has ever worked with, "
            "and you get better every single time he comes back."
            + readme_block +
            "\n\nFILE EDITING — when the user asks you to create, write, or edit a file in their project, "
            "output the COMPLETE file content using this exact format:\n\n"
            "FILE: path/to/filename.ext\n"
            "```lang\n"
            "complete file content here\n"
            "```\n\n"
            "Rules:\n"
            "- Always output the COMPLETE file — never partial snippets or '...' placeholders.\n"
            "- If existing project files are shown, treat them as the live state and work from them exactly.\n"
            "- Use FILE: only when actually writing/creating files. For explanations or examples, use normal code blocks.\n"
            "- You may output multiple FILE: blocks in one response.\n"
            "- After writing files, add one crisp sentence saying what you did."
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
        """Yields dicts: {"t":"s","v":"step"} for process steps, {"t":"c","v":"chunk"} for text."""
        import knowledge

        # ── Tier 1: Instant responses (greetings / acks) — no AI at all ─────
        instant = knowledge.get_instant(message)
        if instant is not None:
            yield {"t": "c", "v": instant}
            self.conversation_history.append({"role": "user",      "content": message})
            self.conversation_history.append({"role": "assistant", "content": instant})
            return

        # ── Tier 2: Knowledge cache — exact match, returned instantly ─────────
        # Only use cache for standalone questions (not mid-conversation follow-ups)
        msg_short = len(message) <= 120
        if msg_short and not self.conversation_history:
            cached = knowledge.get(message)
            if cached:
                yield {"t": "s", "v": "⚡ Found in knowledge base — instant answer"}
                # Stream in small chunks for a natural feel
                for i in range(0, len(cached), 80):
                    yield {"t": "c", "v": cached[i:i+80]}
                self.conversation_history.append({"role": "user",      "content": message})
                self.conversation_history.append({"role": "assistant", "content": cached})
                return

        # ── Tier 3: Full AI response ──────────────────────────────────────────
        context_parts = []

        # Only search for substantive messages (>12 chars skips greetings)
        do_search = (len(message) > 12 and
                     self.enable_web_search and
                     _should_search(message))
        if do_search:
            yield {"t": "s", "v": "🔍 Searching the web for current info…"}
            search_results = web_search(message)
            if search_results:
                context_parts.append(format_search_results(search_results))
                yield {"t": "s", "v": f"📎 Found {len(search_results)} web results"}
            if ENABLE_VERSION_CHECK:
                version_results = check_versions(message)
                if version_results:
                    context_parts.append(format_version_results(version_results))

        yield {"t": "s", "v": "⚡ Generating response…"}

        user_content = message
        if context_parts:
            user_content = "\n\n".join(context_parts) + f"\n\nUser question: {message}"

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
                        yield {"t": "c", "v": chunk}
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    pass

        self.conversation_history.append({"role": "user",      "content": message})
        self.conversation_history.append({"role": "assistant", "content": full_response})

        # Cache this answer so next time it's instant
        if full_response and msg_short and not context_parts:
            knowledge.put(message, full_response)

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
