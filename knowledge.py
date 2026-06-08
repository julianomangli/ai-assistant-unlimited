"""
VIKA Knowledge Base
-------------------
Three-tier speed system:
  1. INSTANT dict  — greetings/acks answered in microseconds, no AI at all
  2. JSON cache    — every answer VIKA generates is saved; repeated questions
                     return instantly from disk regardless of model speed
  3. README pre-build — key Q&A pairs extracted from the GitHub README at
                        startup and cached so common project questions are
                        always instant

The cache grows automatically as VIKA is used ("learns" over time).
"""

import json
import os
import re
import random

CACHE_FILE = "vika_knowledge.json"

# ---------------------------------------------------------------------------
# Tier-1: Instant responses — zero AI, zero latency
# ---------------------------------------------------------------------------
_INSTANT: dict[str, list[str]] = {
    "hello":         ["Hello. Ready when you are.", "Hello — what are we building?", "Hey. What do you need?"],
    "hi":            ["Hi. What are we working on?", "Hey — ready.", "Hi there. What's up?"],
    "hey":           ["Hey. Go ahead.", "Hey — what's on your mind?", "Hey. What do you need?"],
    "hola":          ["Hola. ¿En qué puedo ayudarte?", "Hola. Listo cuando quieras."],
    "how are you":   ["Sharp and ready. What do you need?", "Good. You?", "Online and ready."],
    "whats up":      ["Ready to work. What do you need?", "What's on your mind?"],
    "what's up":     ["Ready to work. What do you need?"],
    "sup":           ["Ready.", "What do you need?"],
    "yo":            ["Hey — what's up?", "Go ahead."],
    "test":          ["Online.", "Working."],
    "ping":          ["Pong."],
    "ok":            ["Got it.", "Understood."],
    "okay":          ["Got it.", "Understood."],
    "k":             ["Got it.", "Noted."],
    "sure":          ["Great. Let's go.", "Sounds good."],
    "yep":           ["Good.", "Alright."],
    "yes":           ["Good.", "Let's do it."],
    "no":            ["Got it.", "Understood."],
    "thanks":        ["Of course.", "Anytime.", "Sure."],
    "thank you":     ["Of course.", "Anytime."],
    "ty":            ["Of course.", "Anytime."],
    "thx":           ["Of course.", "Sure."],
    "nice":          ["Thanks.", "Glad to help."],
    "cool":          ["Let's keep going.", "Good. What's next?"],
    "great":         ["Good. What's next?", "Let's keep going."],
    "perfect":       ["Let's keep going.", "What's next?"],
    "awesome":       ["Let's keep going.", "Good — what's next?"],
    "good":          ["Good. What's next?"],
    "ok cool":       ["Let's keep going.", "What's next?"],
    "sounds good":   ["Good. Let's go.", "Let's do it."],
    "good morning":  ["Good morning. What are we building today?"],
    "good afternoon":["Good afternoon. What's on the agenda?"],
    "good evening":  ["Good evening. Let's build something."],
    "good night":    ["Good night."],
    "goodnight":     ["Good night."],
    "bye":           ["Later.", "See you."],
    "goodbye":       ["Later.", "See you."],
    "see you":       ["See you.", "Later."],
    "later":         ["Later.", "See you."],
    "lol":           ["😄", "Ha."],
    "haha":          ["😄", "Ha."],
    "wow":           ["Right?", "Let's use that. What's next?"],
    "amazing":       ["Let's keep going.", "Good — what's next?"],
}


def get_instant(message: str) -> str | None:
    """Return an instant response for greetings/acks, or None if AI is needed."""
    # Strip trailing punctuation and normalise
    k = re.sub(r"[!?.,'\"]+$", "", message.lower().strip())
    k = re.sub(r"\s+", " ", k)
    responses = _INSTANT.get(k)
    if responses is None:
        return None
    return random.choice(responses) if isinstance(responses, list) else responses


# ---------------------------------------------------------------------------
# Tier-2: Persistent JSON cache — grows with every VIKA response
# ---------------------------------------------------------------------------
_cache: dict[str, str] = {}


def _norm(message: str) -> str:
    return re.sub(r"\s+", " ", message.lower().strip())[:300]


def get(message: str) -> str | None:
    """Return a cached answer, or None if not found."""
    return _cache.get(_norm(message))


def put(message: str, answer: str):
    """Cache an answer VIKA just generated."""
    if not answer or len(answer) < 30:
        return
    _cache[_norm(message)] = answer
    _save()


def size() -> int:
    return len(_cache)


def _save():
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_cache, f, ensure_ascii=False)
    except Exception:
        pass


def load():
    global _cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                _cache = json.load(f)
        except Exception:
            _cache = {}


# ---------------------------------------------------------------------------
# Tier-3: README pre-build — instant answers for common project questions
# ---------------------------------------------------------------------------
def prebuild_from_readme(readme: str):
    """Extract key facts from the README and seed the cache without AI."""
    if not readme:
        return

    _seed_static_faq()
    _extract_readme_facts(readme)
    _save()


def _seed_static_faq():
    """Hard-coded answers that are always true for VIKA."""
    _put_all("what is vika", [
        "what is aria", "what is this", "what is this app",
        "tell me about vika", "tell me about yourself",
    ],
        "VIKA (Versatile Intelligent Knowledge Assistant) is a free, private AI dev studio that runs entirely on your machine. "
        "No data leaves your device. It has two modes:\n\n"
        "- **Chat** — ask anything: code, explanations, debugging, questions\n"
        "- **Build** — describe an app in plain English and VIKA writes it live, with a real preview you can download as ZIP\n\n"
        "The more you work with VIKA, the sharper she gets — she builds context from your messages as you go."
    )

    _put_all("is vika free", [
        "is it free", "is this free", "how much does it cost",
        "does it cost anything", "is there a cost",
    ],
        "**Yes — VIKA is completely free to run locally** (inside Replit, Option B).\n\n"
        "The always-on published site (Option A) costs a flat monthly server fee — no per-message charges ever.\n"
        "Chatting and building are unlimited."
    )

    _put_all("is vika private", [
        "is it private", "is my data safe", "who can see my chats",
        "does this send data", "does it collect data", "is it secure",
        "where does my data go",
    ],
        "**Completely private.** VIKA runs on Ollama — a local AI engine on your own machine.\n\n"
        "Nothing is sent to OpenAI, Google, Anthropic, or any cloud service. "
        "Your conversations never leave your device. The model lives here."
    )

    _put_all("how do i use build mode", [
        "what is build mode", "how does build mode work",
        "how do i build an app", "how do i create an app",
    ],
        "Click the **Build** tab, then describe what you want — for example:\n\n"
        "> *\"Build a to-do list app with dark UI and localStorage\"*\n\n"
        "VIKA will write the code, the Preview tab shows it running live, and the **ZIP** button downloads the whole project. "
        "You can also edit files directly in the editor on the right."
    )

    _put_all("what models are available", [
        "what model are you using", "which model is this",
        "what ai model", "what is the model",
    ],
        "**Local (free, in Replit):** VIKA Core — qwen2.5-coder:3b\n"
        "**Published site:** VIKA Ultra — qwen2.5-coder:14b (much sharper)\n\n"
        "You can switch models using the dropdown in the top-right corner. "
        "To install a new model, run `ollama pull <model-name>` in the Terminal."
    )

    _put_all("how do i connect to github", [
        "how do i push to github", "github integration",
        "how do i use github", "github token", "connect github",
    ],
        "Click the **GitHub icon** in the sidebar:\n\n"
        "1. Paste your Personal Access Token (create one at github.com/settings/tokens — needs `repo` scope)\n"
        "2. Click Connect\n"
        "3. Choose a repo, set your branch, write a commit message → **Commit & Push**\n\n"
        "Your built project files are pushed directly to your GitHub repo."
    )

    _put_all("how do i use the terminal", [
        "what is the terminal", "how do i open the terminal",
        "terminal help",
    ],
        "Click the **>_** icon in the sidebar, or press **Ctrl+`**.\n\n"
        "It's a real shell running inside your project folder. You can run:\n"
        "- `node`, `npm`, `npx`\n"
        "- `python`, `pip`\n"
        "- Any shell command\n\n"
        "**Note:** On the published live site, the terminal is off by default for security. "
        "Set a `TERMINAL_PASSWORD` secret to enable it."
    )

    _put_all("how do i download my project", [
        "how do i download", "zip download", "how do i export",
        "how do i get my files",
    ],
        "Click the **ZIP** button in the top-right corner.\n\n"
        "It downloads your entire project as a ZIP file you can unzip and run anywhere."
    )

    _put_all("how do i use chat mode", [
        "what is chat mode", "how does chat work",
        "what can i ask",
    ],
        "Click the **Chat** tab and type anything:\n\n"
        "- Coding questions\n"
        "- Debug help (paste your error)\n"
        "- Explanations of any concept\n"
        "- Architecture advice\n"
        "- Anything else\n\n"
        "VIKA also has **web search** built in — she'll automatically search for current docs and news when relevant."
    )

    _put_all("how do i make it faster", [
        "why is it slow", "how do i speed it up",
        "make it faster",
    ],
        "Speed depends on the model and whether it's warm:\n\n"
        "1. **First message after restart** — model loads from disk (~20–60s). Subsequent messages are fast.\n"
        "2. **Web search** triggers for coding questions — adds 2–5s. It's automatic for complex questions.\n"
        "3. **Shorter questions** respond faster than long ones.\n"
        "4. **Locally** (VIKA Core, 3B) is fastest. The published site (14B) is smarter but slightly slower per token.\n\n"
        "Simple questions like 'hello' now return instantly from the knowledge cache — no AI needed."
    )

    _put_all("what is the knowledge cache", [
        "how does caching work", "what is prebuild",
        "how does vika learn",
    ],
        "VIKA has a three-tier speed system:\n\n"
        "1. **Instant** — greetings and short acks return in milliseconds, no AI at all\n"
        "2. **Knowledge cache** — every answer VIKA generates is saved to disk. Next time you ask the same thing, it returns instantly\n"
        "3. **README pre-build** — at startup, VIKA reads your GitHub README and seeds common Q&A pairs so project questions are always instant\n\n"
        "The cache grows as you use VIKA — she effectively learns your common questions over time."
    )


def _put_all(primary: str, aliases: list, answer: str):
    """Cache an answer under the primary key and all aliases."""
    put(primary, answer)
    for alias in aliases:
        put(alias, answer)


def _extract_readme_facts(readme: str):
    """Best-effort fact extraction from README text."""
    # Cache the raw README summary for "tell me about the project" style questions
    lines = [l.strip() for l in readme.split("\n") if l.strip() and not l.startswith("#")]
    summary = " ".join(lines[:10])
    if summary:
        put("tell me about the project", summary[:600])
        put("what is this project", summary[:600])
        put("describe the project", summary[:600])


# Load cache on module import
load()
