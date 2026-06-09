"""
VIKA Knowledge Base — Four-Tier Speed System
─────────────────────────────────────────────
Tier 1  INSTANT dict  — greetings/acks answered in microseconds, zero AI
Tier 2  Expert seed   — ~100 pre-written answers across every major tech topic,
                        loaded at startup so first-time visitors are already fast
Tier 3  JSON cache    — every AI answer saved; repeated questions return instantly;
                        shared across all users so the app gets smarter with use
Tier 4  Fuzzy match   — word-overlap scoring finds the best cached answer even
                        when the phrasing differs slightly

The cache grows automatically. The more people use VIKA, the faster and
smarter it becomes for everyone.
"""

import json
import os
import re
import random

CACHE_FILE = "vika_knowledge.json"

# ─────────────────────────────────────────────────────────────────────────────
# Tier-1: Instant responses — zero AI, zero latency
# ─────────────────────────────────────────────────────────────────────────────
_INSTANT: dict[str, list[str]] = {
    "hello":          ["Hello. Ready when you are.", "Hello — what are we building?", "Hey. What do you need?"],
    "hi":             ["Hi. What are we working on?", "Hey — ready.", "Hi there. What's up?"],
    "hey":            ["Hey. Go ahead.", "Hey — what's on your mind?", "Hey. What do you need?"],
    "hola":           ["Hola. ¿En qué puedo ayudarte?", "Hola. Listo cuando quieras."],
    "how are you":    ["Sharp and ready. What do you need?", "Good. You?", "Online and ready."],
    "whats up":       ["Ready to work. What do you need?", "What's on your mind?"],
    "what's up":      ["Ready to work. What do you need?"],
    "sup":            ["Ready.", "What do you need?"],
    "yo":             ["Hey — what's up?", "Go ahead."],
    "test":           ["Online.", "Working."],
    "ping":           ["Pong."],
    "ok":             ["Got it.", "Understood."],
    "okay":           ["Got it.", "Understood."],
    "k":              ["Got it.", "Noted."],
    "sure":           ["Great. Let's go.", "Sounds good."],
    "yep":            ["Good.", "Alright."],
    "yes":            ["Good.", "Let's do it."],
    "no":             ["Got it.", "Understood."],
    "thanks":         ["Of course.", "Anytime.", "Sure."],
    "thank you":      ["Of course.", "Anytime."],
    "ty":             ["Of course.", "Anytime."],
    "thx":            ["Of course.", "Sure."],
    "nice":           ["Thanks.", "Glad to help."],
    "cool":           ["Let's keep going.", "Good. What's next?"],
    "great":          ["Good. What's next?", "Let's keep going."],
    "perfect":        ["Let's keep going.", "What's next?"],
    "awesome":        ["Let's keep going.", "Good — what's next?"],
    "good":           ["Good. What's next?"],
    "ok cool":        ["Let's keep going.", "What's next?"],
    "sounds good":    ["Good. Let's go.", "Let's do it."],
    "good morning":   ["Good morning. What are we building today?"],
    "good afternoon": ["Good afternoon. What's on the agenda?"],
    "good evening":   ["Good evening. Let's build something."],
    "good night":     ["Good night."],
    "goodnight":      ["Good night."],
    "bye":            ["Later.", "See you."],
    "goodbye":        ["Later.", "See you."],
    "see you":        ["See you.", "Later."],
    "later":          ["Later.", "See you."],
    "lol":            ["😄", "Ha."],
    "haha":           ["😄", "Ha."],
    "wow":            ["Right?", "Let's use that. What's next?"],
    "amazing":        ["Let's keep going.", "Good — what's next?"],
}


def get_instant(message: str) -> str | None:
    k = re.sub(r"[!?.,'\"]+$", "", message.lower().strip())
    k = re.sub(r"\s+", " ", k)
    responses = _INSTANT.get(k)
    if responses is None:
        return None
    return random.choice(responses) if isinstance(responses, list) else responses


# ─────────────────────────────────────────────────────────────────────────────
# Tier-2/3: Persistent JSON cache — seeded + grows with every AI answer
# ─────────────────────────────────────────────────────────────────────────────
_cache: dict[str, str] = {}


def _norm(message: str) -> str:
    return re.sub(r"\s+", " ", message.lower().strip())[:300]


def get(message: str) -> str | None:
    return _cache.get(_norm(message))


def put(message: str, answer: str, overwrite: bool = True):
    """Cache an answer. Set overwrite=False to skip if a user answer already exists."""
    if not answer or len(answer) < 30:
        return
    key = _norm(message)
    if not overwrite and key in _cache:
        return
    _cache[key] = answer
    _save()


def size() -> int:
    return len(_cache)


def stats() -> dict:
    return {"total": len(_cache), "file": CACHE_FILE}


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


# ─────────────────────────────────────────────────────────────────────────────
# Tier-4: Fuzzy matching — finds best cached answer by word-overlap scoring
# ─────────────────────────────────────────────────────────────────────────────
_STOP = {"the","a","an","is","are","was","were","be","been","being","have","has",
         "had","do","does","did","will","would","could","should","may","might",
         "to","of","in","on","at","for","with","by","from","about","into","what",
         "how","why","when","where","which","who","i","you","we","it","this","that"}


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2 and w not in _STOP}


def get_fuzzy(message: str, threshold: float = 0.72) -> str | None:
    """Return the best cached answer when word-overlap similarity ≥ threshold."""
    norm = _norm(message)
    if len(norm) < 10:
        return None
    msg_words = _words(norm)
    if len(msg_words) < 2:
        return None

    best_score = 0.0
    best_answer = None
    msg_len = len(norm)

    for key, answer in _cache.items():
        # Quick length sanity check — skip wildly different lengths
        ratio = len(key) / max(msg_len, 1)
        if ratio < 0.25 or ratio > 4.0:
            continue
        key_words = _words(key)
        if not key_words:
            continue
        overlap = len(msg_words & key_words)
        score = overlap / max(len(msg_words), len(key_words))
        if score > best_score:
            best_score = score
            best_answer = answer

    return best_answer if best_score >= threshold else None


# ─────────────────────────────────────────────────────────────────────────────
# Expert seed — pre-written answers across every major topic
# Keys will NOT overwrite existing user/AI-generated answers in the JSON cache
# ─────────────────────────────────────────────────────────────────────────────
def _s(primary: str, aliases: list[str], answer: str):
    """Seed a Q&A pair and its aliases without overwriting user answers."""
    put(primary, answer, overwrite=False)
    for a in aliases:
        put(a, answer, overwrite=False)


def _seed_expert_qa():

    # ── VIKA / App ────────────────────────────────────────────────────────────
    _s("what is vika", ["what is aria","what is this","tell me about vika","tell me about yourself"],
        "**VIKA** (Versatile Intelligent Knowledge Assistant) is a free, private AI dev studio.\n\n"
        "- Runs 100% on your machine via Ollama — nothing sent to any cloud\n"
        "- **Chat mode** — ask anything: code, debugging, explanations\n"
        "- **Build mode** — describe an app, VIKA writes it live with a real preview\n"
        "- **ZIP export** — download any built project instantly\n"
        "- **Knowledge cache** — gets faster the more it's used; answers are shared across all users\n\n"
        "Completely free. No accounts. No API keys.")

    _s("is vika free", ["is it free","how much does it cost","does it cost anything"],
        "**100% free.** No per-message fees, no accounts, no API keys.\n\n"
        "- Run locally (Replit or your own machine) — completely free forever\n"
        "- The hosted public site has a flat server cost — but using it is still free for you\n"
        "- Models are open-source and run on your own hardware")

    _s("is vika private", ["is it private","is my data safe","does this send data","where does my data go"],
        "**Completely private.** VIKA runs on Ollama — a local AI engine.\n\n"
        "Nothing is sent to OpenAI, Google, Anthropic, or any cloud. "
        "Your chats never leave your device. The model is on your machine.")

    # ── Python ────────────────────────────────────────────────────────────────
    _s("what is python", ["explain python","python programming language","what is python used for"],
        "**Python** is a high-level, general-purpose programming language famous for its readable syntax.\n\n"
        "**Used for:** web backends (Django, Flask, FastAPI), data science (pandas, numpy), "
        "machine learning (PyTorch, TensorFlow), scripting, automation, APIs.\n\n"
        "**Key traits:** dynamically typed, interpreted, batteries-included stdlib, massive ecosystem (PyPI).\n\n"
        "```python\n# Hello World\nprint('Hello, World!')\n\n# A function\ndef greet(name: str) -> str:\n    return f'Hello, {name}!'\n```")

    _s("python list comprehension", ["list comprehension python","python comprehension","list comp python"],
        "**List comprehensions** create lists in one expressive line.\n\n"
        "```python\n# Basic\nsquares = [x**2 for x in range(10)]\n\n"
        "# With filter\nevens = [x for x in range(20) if x % 2 == 0]\n\n"
        "# Nested\nmatrix = [[i*j for j in range(1,4)] for i in range(1,4)]\n\n"
        "# Dict comprehension\nword_len = {word: len(word) for word in ['apple','banana','cherry']}\n\n"
        "# Set comprehension\nunique_squares = {x**2 for x in [-2,-1,0,1,2]}\n```\n\n"
        "Prefer comprehensions over `map()`/`filter()` for readability. "
        "For complex logic, a regular `for` loop is clearer.")

    _s("python decorators", ["what are decorators python","python decorator","how to use decorators"],
        "**Decorators** wrap a function to add behaviour without modifying its body.\n\n"
        "```python\nimport functools\n\n# Simple decorator\ndef log_call(func):\n    @functools.wraps(func)\n    def wrapper(*args, **kwargs):\n        print(f'Calling {func.__name__}')\n        result = func(*args, **kwargs)\n        print(f'Done {func.__name__}')\n        return result\n    return wrapper\n\n@log_call\ndef add(a, b):\n    return a + b\n\nadd(1, 2)  # prints Calling add / Done add\n```\n\n"
        "**Decorator with arguments:**\n```python\ndef repeat(n):\n    def decorator(func):\n        @functools.wraps(func)\n        def wrapper(*args, **kwargs):\n            for _ in range(n):\n                func(*args, **kwargs)\n        return wrapper\n    return decorator\n\n@repeat(3)\ndef say_hi():\n    print('Hi!')\n```\n\n"
        "Common built-ins: `@property`, `@staticmethod`, `@classmethod`, `@functools.lru_cache`.")

    _s("python async await", ["python async","asyncio python","async python","python asynchronous"],
        "**Python async/await** runs I/O-bound tasks concurrently without threads.\n\n"
        "```python\nimport asyncio\nimport aiohttp\n\nasync def fetch(url: str) -> str:\n    async with aiohttp.ClientSession() as session:\n        async with session.get(url) as resp:\n            return await resp.text()\n\nasync def main():\n    # Run two requests concurrently\n    results = await asyncio.gather(\n        fetch('https://api.github.com/users/julianomangli'),\n        fetch('https://httpbin.org/get'),\n    )\n    for r in results:\n        print(r[:100])\n\nasyncio.run(main())\n```\n\n"
        "**Rules:** `async def` defines a coroutine. `await` suspends it until the awaitable is done. "
        "Use `asyncio.gather()` to run coroutines concurrently. "
        "For CPU-bound work, use `multiprocessing` instead — async doesn't help there.")

    _s("python classes", ["python class","oop python","object oriented python","python oop"],
        "**Python classes** implement object-oriented programming.\n\n"
        "```python\nfrom dataclasses import dataclass\n\n@dataclass\nclass Point:\n    x: float\n    y: float\n\n    def distance_to(self, other: 'Point') -> float:\n        return ((self.x - other.x)**2 + (self.y - other.y)**2) ** 0.5\n\n# Inheritance\nclass Point3D(Point):\n    z: float = 0.0\n\n    def __repr__(self):\n        return f'Point3D({self.x}, {self.y}, {self.z})'\n\np1 = Point(0, 0)\np2 = Point(3, 4)\nprint(p1.distance_to(p2))  # 5.0\n```\n\n"
        "**Key concepts:** `__init__`, `self`, inheritance, `super()`, `@property`, `@classmethod`, `@staticmethod`, `@dataclass`.")

    _s("python error handling", ["python try except","python exceptions","handle errors python","python try catch"],
        "**Python error handling** uses `try / except / else / finally`.\n\n"
        "```python\ndef read_file(path: str) -> str:\n    try:\n        with open(path) as f:\n            return f.read()\n    except FileNotFoundError:\n        return ''\n    except PermissionError as e:\n        raise RuntimeError(f'No permission: {path}') from e\n    finally:\n        print('read_file done')  # always runs\n\n# Custom exception\nclass ValidationError(ValueError):\n    def __init__(self, field: str, msg: str):\n        super().__init__(f'{field}: {msg}')\n        self.field = field\n\ntry:\n    raise ValidationError('email', 'invalid format')\nexcept ValidationError as e:\n    print(e.field, e)  # email: email: invalid format\n```")

    _s("python virtual environment", ["python venv","python virtualenv","create venv python","python environment"],
        "**Python virtual environments** isolate project dependencies.\n\n"
        "```bash\n# Create\npython -m venv .venv\n\n# Activate\nsource .venv/bin/activate   # Linux / macOS\n.venv\\Scripts\\activate       # Windows\n\n# Install packages\npip install flask requests\n\n# Save dependencies\npip freeze > requirements.txt\n\n# Install from requirements\npip install -r requirements.txt\n\n# Deactivate\ndeactivate\n```\n\n"
        "**Modern alternative:** `uv` (10–100× faster than pip): `uv venv && uv pip install flask`")

    _s("python f strings", ["f strings python","python fstring","string formatting python","format string python"],
        "**f-strings** (Python 3.6+) are the fastest and most readable way to format strings.\n\n"
        "```python\nname = 'VIKA'\nversion = 2.5\n\n# Basic\nprint(f'Hello, {name}!')\n\n# Expressions\nprint(f'2 + 2 = {2 + 2}')\n\n# Format spec\npi = 3.14159\nprint(f'{pi:.2f}')       # 3.14\nprint(f'{1000000:,}')    # 1,000,000\nprint(f'{0.85:.1%}')     # 85.0%\n\n# Debugging (Python 3.8+)\nx = 42\nprint(f'{x=}')           # x=42\n\n# Multiline\nmsg = (\n    f'Name: {name}\\n'\n    f'Version: {version:.1f}'\n)\n```")

    _s("python lambda", ["lambda python","anonymous function python","python lambda function"],
        "**Lambda** creates a small anonymous function in one line.\n\n"
        "```python\n# Basic\ndouble = lambda x: x * 2\nprint(double(5))  # 10\n\n# With sorted / key\npeople = [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]\nsorted_people = sorted(people, key=lambda p: p['age'])\n\n# With map / filter\nnumbers = [1, 2, 3, 4, 5]\nsquares = list(map(lambda x: x**2, numbers))\nevens   = list(filter(lambda x: x % 2 == 0, numbers))\n```\n\n"
        "Prefer named functions for anything longer than one expression — they're easier to debug.")

    # ── JavaScript ────────────────────────────────────────────────────────────
    _s("what is javascript", ["explain javascript","javascript language","what is js"],
        "**JavaScript (JS)** is the language of the web — the only language browsers run natively.\n\n"
        "**Used for:** interactive web pages, web apps (React, Vue, Angular), servers (Node.js), "
        "mobile apps (React Native), desktop apps (Electron).\n\n"
        "```javascript\n// Variables\nconst name = 'VIKA';   // block-scoped, can't reassign\nlet count = 0;         // block-scoped, can reassign\n\n// Arrow function\nconst greet = (name) => `Hello, ${name}!`;\n\n// Async/await\nconst getData = async (url) => {\n  const res = await fetch(url);\n  return res.json();\n};\n```")

    _s("javascript async await", ["js async await","javascript promises async","async await javascript"],
        "**async/await** is the modern way to handle asynchronous JavaScript.\n\n"
        "```javascript\n// fetch with async/await\nasync function getUser(id) {\n  try {\n    const res = await fetch(`/api/users/${id}`);\n    if (!res.ok) throw new Error(`HTTP ${res.status}`);\n    const user = await res.json();\n    return user;\n  } catch (err) {\n    console.error('Failed:', err);\n    throw err;\n  }\n}\n\n// Run multiple requests in parallel\nasync function loadDashboard() {\n  const [user, posts, stats] = await Promise.all([\n    getUser(1),\n    fetch('/api/posts').then(r => r.json()),\n    fetch('/api/stats').then(r => r.json()),\n  ]);\n  return { user, posts, stats };\n}\n```\n\n"
        "**Rule:** `async` functions always return a Promise. `await` pauses execution until the Promise resolves.")

    _s("javascript array methods", ["js array methods","javascript map filter reduce","array methods js"],
        "**JavaScript array methods** — the ones you'll use every day:\n\n"
        "```javascript\nconst nums = [1, 2, 3, 4, 5];\n\n// map — transform each element\nconst doubled = nums.map(n => n * 2);          // [2,4,6,8,10]\n\n// filter — keep elements matching condition\nconst evens = nums.filter(n => n % 2 === 0);   // [2,4]\n\n// reduce — fold into one value\nconst sum = nums.reduce((acc, n) => acc + n, 0); // 15\n\n// find / findIndex\nconst first = nums.find(n => n > 3);            // 4\nconst idx   = nums.findIndex(n => n > 3);       // 3\n\n// some / every\nconst hasEven = nums.some(n => n % 2 === 0);    // true\nconst allPos  = nums.every(n => n > 0);         // true\n\n// flat / flatMap\n[[1,2],[3,4]].flat();                           // [1,2,3,4]\n[1,2,3].flatMap(n => [n, n*2]);                // [1,2,2,4,3,6]\n\n// Chaining\nconst result = nums\n  .filter(n => n % 2 !== 0)\n  .map(n => n ** 2);\n// [1,9,25]\n```")

    _s("javascript arrow functions", ["arrow functions js","js arrow function","es6 arrow functions"],
        "**Arrow functions** are concise function syntax from ES6.\n\n"
        "```javascript\n// Traditional\nfunction add(a, b) { return a + b; }\n\n// Arrow — same thing\nconst add = (a, b) => a + b;\n\n// Single param — parens optional\nconst double = n => n * 2;\n\n// Multi-line — needs explicit return\nconst greet = (name) => {\n  const msg = `Hello, ${name}!`;\n  return msg;\n};\n\n// Returning an object — wrap in parens\nconst makeUser = (name, age) => ({ name, age });\n\n// In array methods\nconst names = users.map(u => u.name);\n```\n\n"
        "**Key difference from `function`:** arrow functions don't have their own `this` — they inherit it from the enclosing scope. Use regular functions for object methods that need `this`.")

    _s("javascript fetch api", ["fetch api js","javascript fetch","how to fetch data javascript","js fetch"],
        "**`fetch()`** is the browser's built-in HTTP client.\n\n"
        "```javascript\n// GET\nconst res = await fetch('/api/data');\nconst data = await res.json();\n\n// POST with JSON\nconst res = await fetch('/api/users', {\n  method: 'POST',\n  headers: { 'Content-Type': 'application/json' },\n  body: JSON.stringify({ name: 'Alice', age: 30 }),\n});\nif (!res.ok) throw new Error(`Error: ${res.status}`);\nconst user = await res.json();\n\n// With error handling\nasync function api(url, options = {}) {\n  const res = await fetch(url, {\n    headers: { 'Content-Type': 'application/json' },\n    ...options,\n  });\n  if (!res.ok) {\n    const err = await res.text();\n    throw new Error(`${res.status}: ${err}`);\n  }\n  return res.json();\n}\n```")

    _s("what is typescript", ["typescript vs javascript","ts vs js","explain typescript","typescript"],
        "**TypeScript** is JavaScript with static types — compiled to plain JS before running.\n\n"
        "```typescript\n// Types\ntype User = {\n  id: number;\n  name: string;\n  email?: string;  // optional\n};\n\n// Generic function\nfunction first<T>(arr: T[]): T | undefined {\n  return arr[0];\n}\n\n// Interface + class\ninterface Shape {\n  area(): number;\n}\n\nclass Circle implements Shape {\n  constructor(private radius: number) {}\n  area() { return Math.PI * this.radius ** 2; }\n}\n\n// Utility types\ntype PartialUser = Partial<User>;\ntype ReadonlyUser = Readonly<User>;\ntype UserName = Pick<User, 'name'>;\n```\n\n"
        "**When to use:** any project with more than one contributor or that will grow. TypeScript catches bugs at compile time that JS only catches at runtime.")

    # ── React ─────────────────────────────────────────────────────────────────
    _s("what is react", ["explain react","react js","reactjs","react library"],
        "**React** is a JavaScript library for building user interfaces, maintained by Meta.\n\n"
        "**Core ideas:**\n"
        "- **Components** — reusable UI pieces (functions that return JSX)\n"
        "- **State** — data that changes; React re-renders when state changes\n"
        "- **Props** — data passed from parent to child components\n"
        "- **Virtual DOM** — React diffs changes and updates only what changed\n\n"
        "```jsx\nimport { useState } from 'react';\n\nfunction Counter() {\n  const [count, setCount] = useState(0);\n  return (\n    <div>\n      <p>Count: {count}</p>\n      <button onClick={() => setCount(c => c + 1)}>+</button>\n    </div>\n  );\n}\n\nexport default Counter;\n```")

    _s("react usestate", ["react use state","usestate hook","react state hook","react hooks state"],
        "**`useState`** adds reactive state to a function component.\n\n"
        "```jsx\nimport { useState } from 'react';\n\nfunction Form() {\n  const [name, setName] = useState('');\n  const [count, setCount] = useState(0);\n  const [items, setItems] = useState([]);\n\n  // Update primitive\n  const handleChange = (e) => setName(e.target.value);\n\n  // Update array (never mutate directly)\n  const addItem = (item) => setItems(prev => [...prev, item]);\n  const removeItem = (id) => setItems(prev => prev.filter(i => i.id !== id));\n\n  // Update object (spread to keep other fields)\n  const [user, setUser] = useState({ name: '', age: 0 });\n  const updateName = (n) => setUser(prev => ({ ...prev, name: n }));\n\n  return <input value={name} onChange={handleChange} />;\n}\n```\n\n"
        "**Rule:** never mutate state directly — always create a new value.")

    _s("react useeffect", ["useeffect hook","react use effect","react side effects","useeffect react"],
        "**`useEffect`** runs side effects (fetching, subscriptions, timers) after render.\n\n"
        "```jsx\nimport { useState, useEffect } from 'react';\n\nfunction UserProfile({ userId }) {\n  const [user, setUser] = useState(null);\n\n  // Runs when userId changes\n  useEffect(() => {\n    let cancelled = false;\n    fetch(`/api/users/${userId}`)\n      .then(r => r.json())\n      .then(data => { if (!cancelled) setUser(data); });\n    \n    return () => { cancelled = true; };  // cleanup\n  }, [userId]);  // dependency array\n\n  // Runs once on mount\n  useEffect(() => {\n    document.title = 'Profile';\n    return () => { document.title = 'App'; };  // on unmount\n  }, []);\n\n  if (!user) return <p>Loading…</p>;\n  return <h1>{user.name}</h1>;\n}\n```\n\n"
        "**Dependency array:** `[]` = mount only, `[a,b]` = when a or b changes, omitted = every render (usually wrong).")

    _s("react components", ["react component","create component react","react functional component"],
        "**React components** are functions that return JSX.\n\n"
        "```jsx\n// Basic component\nfunction Card({ title, children, onClick }) {\n  return (\n    <div className='card' onClick={onClick}>\n      <h2>{title}</h2>\n      <div className='card-body'>{children}</div>\n    </div>\n  );\n}\n\n// Using it\nfunction App() {\n  return (\n    <Card title='Hello' onClick={() => alert('clicked!')}>\n      <p>This is the card body.</p>\n    </Card>\n  );\n}\n\n// With TypeScript\ntype CardProps = {\n  title: string;\n  children: React.ReactNode;\n  onClick?: () => void;\n};\n\nfunction Card({ title, children, onClick }: CardProps) {\n  // ...\n}\n```\n\n"
        "**Best practices:** one component per file, named exports, keep components small and focused.")

    # ── HTML & CSS ────────────────────────────────────────────────────────────
    _s("how to center a div", ["center div css","css center element","center div","flexbox center"],
        "**Three modern ways to center in CSS:**\n\n"
        "```css\n/* 1. Flexbox (most common) */\n.container {\n  display: flex;\n  justify-content: center;  /* horizontal */\n  align-items: center;      /* vertical */\n  min-height: 100vh;\n}\n\n/* 2. Grid */\n.container {\n  display: grid;\n  place-items: center;\n  min-height: 100vh;\n}\n\n/* 3. Absolute positioning */\n.container { position: relative; }\n.centered {\n  position: absolute;\n  top: 50%; left: 50%;\n  transform: translate(-50%, -50%);\n}\n```\n\n"
        "Flexbox or Grid are the go-to choices. Absolute positioning is useful when flexbox/grid isn't available on the parent.")

    _s("css flexbox", ["flexbox css","css flex","flex layout","display flex"],
        "**CSS Flexbox** — one-dimensional layout (row or column).\n\n"
        "```css\n.container {\n  display: flex;\n  flex-direction: row;          /* row | row-reverse | column | column-reverse */\n  justify-content: space-between; /* main axis: flex-start|center|space-between|space-around|space-evenly */\n  align-items: center;          /* cross axis: flex-start|center|flex-end|stretch|baseline */\n  flex-wrap: wrap;              /* allow wrapping */\n  gap: 1rem;                    /* space between items */\n}\n\n.item {\n  flex: 1;            /* grow to fill space equally */\n  flex: 0 0 200px;    /* don't grow, don't shrink, 200px wide */\n  align-self: flex-end; /* override align-items for this item */\n  order: 2;           /* reorder visually */\n}\n```\n\n"
        "**Quick recipes:** `justify-content: center` + `align-items: center` = perfectly centred. "
        "`flex: 1` on all items = equal widths. `margin-left: auto` on last item = push to far right.")

    _s("css grid", ["css grid layout","display grid","grid css","css grid tutorial"],
        "**CSS Grid** — two-dimensional layout (rows AND columns).\n\n"
        "```css\n.grid {\n  display: grid;\n  grid-template-columns: repeat(3, 1fr);  /* 3 equal columns */\n  grid-template-columns: 200px auto 200px; /* fixed-auto-fixed */\n  grid-template-rows: auto;               /* rows size to content */\n  gap: 1.5rem;                            /* row and column gap */\n}\n\n/* Responsive grid without media queries */\n.grid {\n  display: grid;\n  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));\n  gap: 1rem;\n}\n\n/* Spanning columns/rows */\n.hero {\n  grid-column: 1 / -1;   /* span full width */\n  grid-row: 1 / 3;       /* span 2 rows */\n}\n\n/* Named areas */\n.layout {\n  grid-template-areas:\n    'header header'\n    'sidebar main'\n    'footer footer';\n}\n.header { grid-area: header; }\n```")

    _s("css media queries", ["media queries css","responsive css","responsive design css","breakpoints css"],
        "**CSS media queries** make layouts adapt to screen size.\n\n"
        "```css\n/* Mobile-first approach (recommended) */\n.container { padding: 1rem; }         /* base: mobile */\n\n@media (min-width: 640px) {           /* sm — tablet portrait */\n  .container { padding: 1.5rem; }\n}\n\n@media (min-width: 1024px) {          /* lg — desktop */\n  .container {\n    max-width: 1280px;\n    margin: 0 auto;\n    padding: 2rem;\n  }\n}\n\n/* Common breakpoints (Tailwind-style) */\n/* sm: 640px  |  md: 768px  |  lg: 1024px  |  xl: 1280px  |  2xl: 1536px */\n\n/* Other queries */\n@media (prefers-color-scheme: dark) { /* dark mode */ }\n@media (prefers-reduced-motion: reduce) { /* accessibility */ }\n@media print { /* print styles */ }\n```")

    _s("css variables", ["css custom properties","css vars","custom properties css","css var"],
        "**CSS custom properties** (variables) let you reuse values and theme your app.\n\n"
        "```css\n/* Define on :root for global scope */\n:root {\n  --color-primary: #00ff88;\n  --color-bg: #0d0d0d;\n  --color-text: #e0e0e0;\n  --font-size-base: 16px;\n  --spacing-md: 1rem;\n  --radius: 0.5rem;\n}\n\n/* Use anywhere */\n.button {\n  background: var(--color-primary);\n  padding: var(--spacing-md);\n  border-radius: var(--radius);\n  font-size: var(--font-size-base);\n}\n\n/* Dark mode via class */\n.dark {\n  --color-bg: #ffffff;\n  --color-text: #0d0d0d;\n}\n\n/* Fallback value */\ncolor: var(--color-accent, #ff6600);\n\n/* Change with JavaScript */\ndocument.documentElement.style.setProperty('--color-primary', '#ff0000');\n```")

    # ── Node.js / Backend ─────────────────────────────────────────────────────
    _s("what is nodejs", ["node js","nodejs","what is node","explain node js"],
        "**Node.js** is a JavaScript runtime built on Chrome's V8 engine — runs JS outside the browser.\n\n"
        "**Used for:** REST APIs, real-time apps (chat, live updates), CLI tools, build tooling (webpack, vite), BFF layers.\n\n"
        "```javascript\n// HTTP server (built-in)\nconst http = require('http');\nhttp.createServer((req, res) => {\n  res.writeHead(200, {'Content-Type': 'text/plain'});\n  res.end('Hello from Node!');\n}).listen(3000);\n\n// Modern: use Express or Fastify instead\n```\n\n"
        "**Key features:** non-blocking I/O (handles thousands of concurrent connections), "
        "npm ecosystem (2M+ packages), same language on front and back end.")

    _s("how to create a rest api", ["create rest api","build rest api","rest api nodejs","rest api python flask"],
        "**REST API with Express (Node.js):**\n\n"
        "```javascript\nimport express from 'express';\nconst app = express();\napp.use(express.json());\n\nlet items = [];\n\napp.get('/api/items', (req, res) => res.json(items));\n\napp.post('/api/items', (req, res) => {\n  const item = { id: Date.now(), ...req.body };\n  items.push(item);\n  res.status(201).json(item);\n});\n\napp.put('/api/items/:id', (req, res) => {\n  const idx = items.findIndex(i => i.id === +req.params.id);\n  if (idx === -1) return res.status(404).json({ error: 'Not found' });\n  items[idx] = { ...items[idx], ...req.body };\n  res.json(items[idx]);\n});\n\napp.delete('/api/items/:id', (req, res) => {\n  items = items.filter(i => i.id !== +req.params.id);\n  res.status(204).send();\n});\n\napp.listen(3000, () => console.log('API running on :3000'));\n```\n\n"
        "**With Flask (Python):**\n```python\nfrom flask import Flask, request, jsonify\napp = Flask(__name__)\n\n@app.get('/api/items')\ndef list_items():\n    return jsonify(items)\n\n@app.post('/api/items')\ndef create_item():\n    data = request.get_json()\n    items.append(data)\n    return jsonify(data), 201\n```")

    _s("npm vs yarn vs pnpm", ["package manager node","npm yarn pnpm","which package manager"],
        "**Node.js package managers compared:**\n\n"
        "| | npm | yarn | pnpm |\n|---|---|---|---|\n| Speed | Baseline | Faster (cache) | **Fastest** |\n| Disk use | High | Medium | **Lowest** (hard links) |\n| Lockfile | `package-lock.json` | `yarn.lock` | `pnpm-lock.yaml` |\n| Workspaces | ✓ | ✓ | **Best-in-class** |\n| Built-in? | Yes (with Node) | No | No |\n\n"
        "**Recommendation:** use **pnpm** for new projects (fastest, saves disk, great monorepo support).\n\n"
        "```bash\n# Install pnpm\nnpm install -g pnpm\n\n# Same commands, faster\npnpm install\npnpm add react\npnpm run dev\n```")

    # ── Databases ─────────────────────────────────────────────────────────────
    _s("what is sql", ["sql language","explain sql","sql basics","structured query language"],
        "**SQL** (Structured Query Language) queries and manages relational databases.\n\n"
        "```sql\n-- SELECT\nSELECT name, email FROM users WHERE age > 18 ORDER BY name LIMIT 10;\n\n-- JOIN\nSELECT u.name, o.total\nFROM users u\nJOIN orders o ON o.user_id = u.id\nWHERE o.total > 100;\n\n-- INSERT\nINSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');\n\n-- UPDATE\nUPDATE users SET email = 'new@email.com' WHERE id = 1;\n\n-- DELETE\nDELETE FROM users WHERE id = 1;\n\n-- Aggregate\nSELECT COUNT(*), AVG(total), MAX(total)\nFROM orders\nGROUP BY user_id\nHAVING COUNT(*) > 5;\n```")

    _s("sql vs nosql", ["nosql vs sql","when to use nosql","relational vs nosql","mongodb vs postgresql"],
        "**SQL vs NoSQL — when to use which:**\n\n"
        "**Use SQL (PostgreSQL, MySQL, SQLite) when:**\n"
        "- Data has clear relationships (users → orders → products)\n"
        "- You need transactions and ACID guarantees\n"
        "- Data structure is well-defined and stable\n"
        "- You need complex queries with joins\n\n"
        "**Use NoSQL (MongoDB, Redis, DynamoDB) when:**\n"
        "- Data is document-shaped and varies per record\n"
        "- You need massive horizontal scale (millions of writes/sec)\n"
        "- Schema needs to evolve rapidly\n"
        "- Key-value lookups only (Redis for caching)\n\n"
        "**Default choice:** **PostgreSQL** for almost everything. It's battle-tested, free, supports JSON, "
        "full-text search, and scales well. Add Redis for caching/sessions on top.")

    _s("what is an index in database", ["database index","sql index","index database","how do indexes work"],
        "**Database indexes** speed up queries by creating a sorted data structure for a column.\n\n"
        "```sql\n-- Without index: full table scan O(n)\nSELECT * FROM orders WHERE user_id = 123;  -- scans every row\n\n-- Create index\nCREATE INDEX idx_orders_user_id ON orders(user_id);\n-- Now the query is O(log n) — much faster\n\n-- Composite index (order matters)\nCREATE INDEX idx_orders_user_date ON orders(user_id, created_at);\n\n-- Unique index\nCREATE UNIQUE INDEX idx_users_email ON users(email);\n\n-- Check existing indexes\nSELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'orders';\n\n-- EXPLAIN to see if index is used\nEXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123;\n```\n\n"
        "**Rules:** index columns used in `WHERE`, `JOIN ON`, `ORDER BY`. Don't over-index — each index slows down writes.")

    # ── Git ───────────────────────────────────────────────────────────────────
    _s("git commands", ["git basics","basic git commands","git cheat sheet","how to use git"],
        "**Essential Git commands:**\n\n"
        "```bash\n# Setup\ngit config --global user.name 'Your Name'\ngit config --global user.email 'you@example.com'\n\n# Start\ngit init\ngit clone https://github.com/user/repo.git\n\n# Daily workflow\ngit status                  # what changed\ngit add .                   # stage everything\ngit add file.py             # stage one file\ngit commit -m 'feat: add login'\ngit push origin main\ngit pull                    # fetch + merge\n\n# Branches\ngit checkout -b feature/new-thing   # create & switch\ngit switch main                     # switch branch\ngit merge feature/new-thing         # merge into current\ngit branch -d feature/new-thing     # delete branch\n\n# Undo\ngit restore file.py         # discard unstaged changes\ngit reset HEAD~1            # undo last commit (keep changes)\ngit revert abc123           # safe undo (makes new commit)\n\n# Inspect\ngit log --oneline -10\ngit diff HEAD\ngit stash / git stash pop\n```")

    _s("git merge vs rebase", ["rebase vs merge git","git rebase","when to rebase git","merge rebase difference"],
        "**Git merge vs rebase:**\n\n"
        "**Merge** — creates a merge commit, preserves exact history:\n"
        "```bash\ngit checkout main\ngit merge feature/login\n# Result: non-linear history with merge commit\n```\n\n"
        "**Rebase** — replays commits on top of target, linear history:\n"
        "```bash\ngit checkout feature/login\ngit rebase main\n# Result: clean linear history, no merge commit\n```\n\n"
        "**Rule of thumb:**\n"
        "- `merge` for integrating finished features into `main` (or for shared branches)\n"
        "- `rebase` to update a feature branch with changes from `main` (local branches only)\n"
        "- **Never rebase commits already pushed to a shared branch** — it rewrites history")

    # ── Docker ────────────────────────────────────────────────────────────────
    _s("what is docker", ["explain docker","docker containers","docker basics","docker tutorial"],
        "**Docker** packages apps and their dependencies into portable containers.\n\n"
        "**Key concepts:**\n"
        "- **Image** — blueprint (like a class)\n"
        "- **Container** — running instance of an image (like an object)\n"
        "- **Dockerfile** — instructions to build an image\n"
        "- **Docker Compose** — run multi-container apps with one command\n\n"
        "```bash\n# Basic commands\ndocker build -t my-app .          # build image from Dockerfile\ndocker run -p 8080:5000 my-app    # run container, map ports\ndocker run -d my-app              # run detached (background)\ndocker ps                         # list running containers\ndocker logs <container-id>        # view logs\ndocker stop <container-id>        # stop container\ndocker exec -it <id> sh           # shell inside container\n\n# Docker Compose\ndocker compose up                 # start all services\ndocker compose up --build         # rebuild and start\ndocker compose down               # stop and remove containers\n```")

    _s("dockerfile basics", ["how to write dockerfile","dockerfile tutorial","create dockerfile","dockerfile example"],
        "**A production-ready Dockerfile:**\n\n"
        "```dockerfile\n# Python app\nFROM python:3.11-slim\n\nWORKDIR /app\n\n# Install deps first (cached layer)\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\n\n# Copy source\nCOPY . .\n\n# Non-root user for security\nRUN useradd -m appuser && chown -R appuser /app\nUSER appuser\n\nEXPOSE 8000\nCMD [\"gunicorn\", \"app:app\", \"--bind\", \"0.0.0.0:8000\", \"--workers\", \"2\"]\n```\n\n"
        "```dockerfile\n# Node.js app\nFROM node:20-alpine\nWORKDIR /app\nCOPY package*.json .\nRUN npm ci --only=production\nCOPY . .\nEXPOSE 3000\nCMD [\"node\", \"server.js\"]\n```\n\n"
        "**Best practices:** use specific tags (not `latest`), small base images (`slim`, `alpine`), "
        "copy `requirements.txt` / `package.json` before source code (better layer caching), non-root user.")

    # ── APIs & HTTP ───────────────────────────────────────────────────────────
    _s("what is a rest api", ["rest api","restful api","what is rest","explain rest api"],
        "**REST** (Representational State Transfer) is an architectural style for web APIs.\n\n"
        "**Principles:**\n"
        "- Resources identified by URLs (`/api/users/123`)\n"
        "- HTTP verbs convey action: `GET` read, `POST` create, `PUT/PATCH` update, `DELETE` delete\n"
        "- Stateless — server doesn't store session between requests\n"
        "- Returns JSON (usually)\n\n"
        "```\nGET    /api/users          → list all users\nGET    /api/users/123      → get user 123\nPOST   /api/users          → create user (body has data)\nPUT    /api/users/123      → replace user 123\nPATCH  /api/users/123      → update fields of user 123\nDELETE /api/users/123      → delete user 123\n```\n\n"
        "**HTTP Status codes to know:**\n"
        "`200 OK` · `201 Created` · `204 No Content` · `400 Bad Request` · "
        "`401 Unauthorized` · `403 Forbidden` · `404 Not Found` · `422 Unprocessable` · `500 Server Error`")

    _s("http status codes", ["http codes","status codes","response codes http","http error codes"],
        "**Common HTTP status codes:**\n\n"
        "**2xx Success**\n"
        "- `200 OK` — standard success\n"
        "- `201 Created` — resource created (POST)\n"
        "- `204 No Content` — success, no body (DELETE)\n\n"
        "**3xx Redirect**\n"
        "- `301 Moved Permanently` — SEO-friendly redirect\n"
        "- `302 Found` — temporary redirect\n"
        "- `304 Not Modified` — use cached version\n\n"
        "**4xx Client Error**\n"
        "- `400 Bad Request` — malformed request\n"
        "- `401 Unauthorized` — not authenticated\n"
        "- `403 Forbidden` — authenticated but no permission\n"
        "- `404 Not Found` — resource doesn't exist\n"
        "- `409 Conflict` — duplicate resource\n"
        "- `422 Unprocessable Entity` — validation failed\n"
        "- `429 Too Many Requests` — rate limited\n\n"
        "**5xx Server Error**\n"
        "- `500 Internal Server Error` — unhandled exception\n"
        "- `502 Bad Gateway` — upstream server error\n"
        "- `503 Service Unavailable` — server overloaded/down")

    _s("what is graphql", ["graphql vs rest","explain graphql","graphql api"],
        "**GraphQL** is a query language for APIs where the client specifies exactly what data it needs.\n\n"
        "```graphql\n# Query — ask for exactly what you need\nquery GetUser {\n  user(id: \"123\") {\n    name\n    email\n    posts(last: 5) {\n      title\n      createdAt\n    }\n  }\n}\n\n# Mutation — modify data\nmutation CreatePost {\n  createPost(input: { title: \"Hello\", body: \"World\" }) {\n    id\n    title\n  }\n}\n```\n\n"
        "**GraphQL vs REST:**\n"
        "- REST: multiple endpoints, fixed response shape → over/under fetching\n"
        "- GraphQL: one endpoint, client defines shape → exactly what you asked for\n\n"
        "**Use GraphQL when:** you have many clients (mobile, web) with different data needs, complex nested data, rapid UI iteration.")

    # ── Algorithms & CS ───────────────────────────────────────────────────────
    _s("what is big o notation", ["big o","time complexity","space complexity","algorithm complexity","o(n)"],
        "**Big O notation** describes how an algorithm's time or space grows with input size.\n\n"
        "| Notation | Name | Example | 1000 inputs |\n|---|---|---|---|\n"
        "| O(1) | Constant | Hash lookup, array index | 1 op |\n"
        "| O(log n) | Logarithmic | Binary search | ~10 ops |\n"
        "| O(n) | Linear | Loop through array | 1,000 ops |\n"
        "| O(n log n) | Linearithmic | Merge sort, quicksort | ~10,000 ops |\n"
        "| O(n²) | Quadratic | Nested loops | 1,000,000 ops |\n"
        "| O(2ⁿ) | Exponential | Recursive Fibonacci | Astronomical |\n\n"
        "```python\n# O(1) — constant\ndef get_first(arr): return arr[0]\n\n# O(n) — linear\ndef find(arr, val): return any(x == val for x in arr)\n\n# O(n²) — quadratic — avoid on large inputs\ndef has_duplicate(arr):\n    for i in arr:\n        for j in arr:\n            if i != j and i == j: return True\n```")

    _s("what is recursion", ["recursion explained","recursive function","how does recursion work"],
        "**Recursion** — a function that calls itself, with a base case to stop.\n\n"
        "```python\n# Factorial\ndef factorial(n: int) -> int:\n    if n <= 1:          # base case — stops recursion\n        return 1\n    return n * factorial(n - 1)  # recursive case\n\n# factorial(5) = 5 * 4 * 3 * 2 * 1 = 120\n\n# Fibonacci (naive — exponential)\ndef fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)\n\n# Fibonacci (memoised — O(n))\nfrom functools import lru_cache\n@lru_cache(maxsize=None)\ndef fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)\n\n# Tree traversal (classic recursive problem)\ndef sum_tree(node):\n    if node is None: return 0\n    return node.val + sum_tree(node.left) + sum_tree(node.right)\n```\n\n"
        "**Rules:** always have a base case, ensure progress toward it, watch stack depth (Python default: 1000).")

    _s("what is json", ["json format","explain json","json data format","json vs xml"],
        "**JSON** (JavaScript Object Notation) — the universal data exchange format.\n\n"
        "```json\n{\n  \"name\": \"Alice\",\n  \"age\": 30,\n  \"active\": true,\n  \"score\": null,\n  \"tags\": [\"admin\", \"user\"],\n  \"address\": {\n    \"city\": \"Buenos Aires\",\n    \"country\": \"Argentina\"\n  }\n}\n```\n\n"
        "**Types:** string, number, boolean, null, array, object.\n\n"
        "```python\nimport json\n# Python dict → JSON string\ntext = json.dumps({'name': 'Alice'}, indent=2)\n# JSON string → Python dict\ndata = json.loads(text)\n# Read/write files\nwith open('data.json') as f: data = json.load(f)\nwith open('data.json', 'w') as f: json.dump(data, f)\n```\n\n"
        "```javascript\n// JS — built-in\nconst text = JSON.stringify({ name: 'Alice' });\nconst data = JSON.parse(text);\n```")

    # ── Architecture / Concepts ───────────────────────────────────────────────
    _s("what is an api", ["api meaning","what does api stand for","explain api","what is api"],
        "**API** (Application Programming Interface) — a defined way for software to talk to other software.\n\n"
        "**Analogy:** a restaurant menu. You (client) order from the menu (API), the kitchen (server) "
        "prepares it and sends it back. You don't need to know how the kitchen works.\n\n"
        "**Types:**\n"
        "- **REST API** — HTTP-based, uses URLs + verbs, returns JSON (most common)\n"
        "- **GraphQL** — one endpoint, client specifies exact data shape\n"
        "- **WebSocket** — persistent connection for real-time two-way communication\n"
        "- **SDK/Library API** — functions you call in your code (`list.append()`)\n\n"
        "**Example — calling GitHub's API:**\n"
        "```bash\ncurl https://api.github.com/users/julianomangli\n# Returns JSON with name, repos, followers, etc.\n```")

    _s("what is a webhook", ["webhooks","webhook vs api","how webhooks work","explain webhooks"],
        "**Webhooks** — reverse APIs. Instead of you polling ('any updates?'), "
        "the server calls your URL when something happens.\n\n"
        "**API polling (inefficient):**\n"
        "```\nYou → GitHub: 'Any new commits?'\nGitHub → You: 'No'\nYou → GitHub: 'Any new commits?' (every minute forever)\n```\n\n"
        "**Webhook (efficient):**\n"
        "```\nYou → GitHub: 'Call my URL when there's a push'\nGitHub → Your URL: 'Here's the new commit data'\n```\n\n"
        "```python\n# Flask webhook receiver\n@app.post('/webhook/github')\ndef handle_push():\n    data = request.get_json()\n    branch = data['ref'].split('/')[-1]\n    commits = data['commits']\n    print(f'{len(commits)} new commits on {branch}')\n    return '', 200\n```\n\n"
        "**Use for:** CI/CD triggers, payment notifications (Stripe), chat bots, form submissions.")

    _s("what is cors", ["cors error","cors headers","fix cors","cors javascript","access-control-allow-origin"],
        "**CORS** (Cross-Origin Resource Sharing) — browser security that blocks requests to a different domain.\n\n"
        "**The error:** `Access to fetch at 'http://api.com' from 'http://app.com' has been blocked by CORS`\n\n"
        "**Fix — add headers on your server:**\n\n"
        "```python\n# Flask\nfrom flask_cors import CORS\napp = Flask(__name__)\nCORS(app)  # allow all, or:\nCORS(app, resources={r'/api/*': {'origins': 'https://yoursite.com'}})\n```\n\n"
        "```javascript\n// Express\nconst cors = require('cors');\napp.use(cors());  // allow all\napp.use(cors({ origin: 'https://yoursite.com' }));  // specific\n\n// Manual headers\nres.setHeader('Access-Control-Allow-Origin', '*');\nres.setHeader('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE');\n```\n\n"
        "**Note:** CORS is enforced by browsers only — server-to-server calls are never blocked by CORS.")

    _s("what is microservices", ["microservices vs monolith","monolith architecture","microservice architecture","when to use microservices"],
        "**Monolith vs Microservices:**\n\n"
        "**Monolith** — one codebase, deployed as one unit:\n"
        "- ✅ Simple to develop, deploy, debug\n"
        "- ✅ No network latency between components\n"
        "- ❌ Hard to scale individual parts\n"
        "- ❌ One bug can crash everything\n\n"
        "**Microservices** — many small services, each deployed independently:\n"
        "- ✅ Scale each service independently\n"
        "- ✅ Teams can work on separate services\n"
        "- ✅ One service failing doesn't take down the whole app\n"
        "- ❌ Network calls between services add latency\n"
        "- ❌ Much harder to develop and debug\n\n"
        "**The rule:** start with a well-structured monolith. "
        "Split into microservices only when you have a real scaling or team problem. "
        "Netflix, Amazon → microservices. Your startup → monolith first.")

    _s("what is a database", ["explain database","types of databases","what is db","database basics"],
        "**A database** stores, organises, and retrieves data reliably.\n\n"
        "**Main types:**\n\n"
        "| Type | Examples | Best for |\n|---|---|---|\n"
        "| **Relational (SQL)** | PostgreSQL, MySQL, SQLite | Structured data with relationships |\n"
        "| **Document** | MongoDB, Firestore | JSON-like flexible documents |\n"
        "| **Key-Value** | Redis, DynamoDB | Fast lookups, caching, sessions |\n"
        "| **Column** | Cassandra, BigQuery | Analytics, time-series, huge scale |\n"
        "| **Graph** | Neo4j | Relationships (social networks, recommendations) |\n"
        "| **Search** | Elasticsearch | Full-text search |\n\n"
        "**Start with PostgreSQL** — it handles 95% of use cases, is free, battle-tested, "
        "and supports JSON, full-text search, and extensions.")

    # ── Dev Tools ─────────────────────────────────────────────────────────────
    _s("what is git", ["explain git","version control git","why use git","what does git do"],
        "**Git** is a distributed version control system — it tracks changes to your code over time.\n\n"
        "**Why it matters:**\n"
        "- Go back to any previous version of your code\n"
        "- Work on multiple features simultaneously (branches)\n"
        "- Collaborate with others without overwriting each other\n"
        "- See who changed what and why (commit history)\n\n"
        "```bash\ngit init                     # start tracking a folder\ngit add .                    # stage your changes\ngit commit -m 'first commit' # save a snapshot\ngit log --oneline            # see history\ngit checkout abc123          # go back to that snapshot\n```\n\n"
        "**GitHub/GitLab/Bitbucket** are hosting platforms for Git repos — not Git itself. "
        "Git is the tool; GitHub is where you store and share it.")

    _s("what is docker compose", ["docker-compose","compose docker","docker compose tutorial"],
        "**Docker Compose** runs multi-container apps with a single command.\n\n"
        "```yaml\n# docker-compose.yml\nservices:\n  web:\n    build: .\n    ports:\n      - '8080:5000'\n    environment:\n      DATABASE_URL: postgresql://db/myapp\n    depends_on:\n      db:\n        condition: service_healthy\n\n  db:\n    image: postgres:16\n    environment:\n      POSTGRES_DB: myapp\n      POSTGRES_PASSWORD: secret\n    volumes:\n      - pg_data:/var/lib/postgresql/data\n    healthcheck:\n      test: ['CMD', 'pg_isready', '-U', 'postgres']\n      interval: 5s\n      retries: 5\n\nvolumes:\n  pg_data:\n```\n\n"
        "```bash\ndocker compose up          # start everything\ndocker compose up --build  # rebuild images first\ndocker compose down        # stop and remove\ndocker compose logs -f web # tail logs for one service\n```")

    _s("what is ci cd", ["cicd","continuous integration","continuous deployment","ci cd pipeline","github actions"],
        "**CI/CD** automates testing and deployment so code goes from push to production reliably.\n\n"
        "**CI (Continuous Integration):** every push runs tests automatically.\n"
        "**CD (Continuous Delivery/Deployment):** passing tests automatically deploy to production.\n\n"
        "```yaml\n# .github/workflows/deploy.yml (GitHub Actions)\nname: Deploy\non:\n  push:\n    branches: [main]\n\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with: { python-version: '3.11' }\n      - run: pip install -r requirements.txt\n      - run: pytest\n\n  deploy:\n    needs: test\n    runs-on: ubuntu-latest\n    steps:\n      - name: Deploy to server\n        run: ssh deploy@server 'cd app && git pull && systemctl restart app'\n```\n\n"
        "**Popular tools:** GitHub Actions (free), GitLab CI, CircleCI, Jenkins.")

    _s("what is serverless", ["serverless computing","lambda functions","serverless vs server","cloud functions"],
        "**Serverless** means you write functions; the cloud provider handles servers, scaling, and availability.\n\n"
        "```python\n# AWS Lambda handler\ndef handler(event, context):\n    name = event.get('name', 'World')\n    return {\n        'statusCode': 200,\n        'body': f'Hello, {name}!'\n    }\n```\n\n"
        "**Providers:** AWS Lambda, Google Cloud Functions, Vercel Functions, Netlify Functions, Cloudflare Workers.\n\n"
        "**When to use:** event-driven tasks (image processing, email sending, webhooks), "
        "APIs with variable traffic, scheduled jobs.\n\n"
        "**Pros:** zero infrastructure, auto-scales to zero, pay per request.\n"
        "**Cons:** cold starts, stateless, 15min max execution, vendor lock-in.")

    # ── Web Security ──────────────────────────────────────────────────────────
    _s("what is jwt", ["json web token","jwt authentication","how jwt works","jwt token"],
        "**JWT** (JSON Web Token) — a self-contained token for authentication.\n\n"
        "**Structure:** `header.payload.signature` (base64-encoded, dot-separated)\n\n"
        "```python\nimport jwt  # pip install PyJWT\nfrom datetime import datetime, timedelta\n\nSECRET = 'your-secret-key'\n\n# Create token\ndef create_token(user_id: int) -> str:\n    payload = {\n        'sub': user_id,\n        'exp': datetime.utcnow() + timedelta(hours=24),\n    }\n    return jwt.encode(payload, SECRET, algorithm='HS256')\n\n# Verify token\ndef verify_token(token: str) -> dict:\n    return jwt.decode(token, SECRET, algorithms=['HS256'])\n    # Raises jwt.ExpiredSignatureError, jwt.InvalidTokenError\n```\n\n"
        "```javascript\n// Node.js\nconst jwt = require('jsonwebtoken');\nconst token = jwt.sign({ userId: 123 }, 'secret', { expiresIn: '24h' });\nconst payload = jwt.verify(token, 'secret');\n```\n\n"
        "**Important:** JWTs are signed, not encrypted. Don't put sensitive data in them. Store in `httpOnly` cookies, not localStorage.")

    _s("sql injection", ["prevent sql injection","sql injection attack","parameterized queries","sql security"],
        "**SQL injection** is the #1 web vulnerability — never build SQL with string concatenation.\n\n"
        "```python\n# DANGEROUS — never do this\nusername = request.form['username']\nquery = f\"SELECT * FROM users WHERE username = '{username}'\"\n# Attacker input: ' OR '1'='1 → returns all users!\n\n# SAFE — use parameterised queries\n# SQLite / SQLAlchemy core\ncursor.execute('SELECT * FROM users WHERE username = ?', (username,))\n\n# SQLAlchemy ORM — automatically safe\nuser = session.query(User).filter(User.username == username).first()\n\n# psycopg2\ncursor.execute('SELECT * FROM users WHERE username = %s', (username,))\n```\n\n"
        "**Rule:** always use parameterised queries or an ORM. Never concatenate user input into SQL. Same applies to NoSQL injection.")

    # ── Practical / Common Tasks ──────────────────────────────────────────────
    _s("how to read a file python", ["read file python","python open file","python file read","python read text file"],
        "**Reading files in Python:**\n\n"
        "```python\n# Read entire file\nwith open('file.txt', 'r', encoding='utf-8') as f:\n    content = f.read()\n\n# Read line by line (memory efficient for large files)\nwith open('file.txt') as f:\n    for line in f:\n        print(line.rstrip())\n\n# Read all lines into list\nwith open('file.txt') as f:\n    lines = f.readlines()\n\n# Write file\nwith open('output.txt', 'w', encoding='utf-8') as f:\n    f.write('Hello, World!\\n')\n\n# Append\nwith open('log.txt', 'a') as f:\n    f.write('new entry\\n')\n\n# JSON\nimport json\nwith open('data.json') as f: data = json.load(f)\nwith open('data.json', 'w') as f: json.dump(data, f, indent=2)\n```\n\n"
        "Always use `with` — it guarantees the file is closed even if an error occurs.")

    _s("how to make http request python", ["python requests","python http request","requests library python","http get python"],
        "**HTTP requests in Python with `requests`:**\n\n"
        "```python\nimport requests\n\n# GET\nres = requests.get('https://api.github.com/users/julianomangli')\nres.raise_for_status()  # raises on 4xx/5xx\ndata = res.json()\nprint(data['name'])\n\n# GET with params → /search?q=python&page=1\nres = requests.get('https://api.example.com/search', params={'q': 'python', 'page': 1})\n\n# POST JSON\nres = requests.post(\n    'https://api.example.com/users',\n    json={'name': 'Alice', 'email': 'alice@example.com'},\n    headers={'Authorization': 'Bearer token123'},\n    timeout=10,\n)\n\n# Session (reuses TCP connections, shares headers)\nwith requests.Session() as s:\n    s.headers['Authorization'] = 'Bearer token'\n    users = s.get('/api/users').json()\n    posts = s.get('/api/posts').json()\n```")

    _s("how to use environment variables", ["env variables","dotenv","python dotenv","environment variables python","process.env"],
        "**Environment variables** — store secrets and config outside your code.\n\n"
        "```bash\n# .env file (never commit to git!)\nDATABASE_URL=postgresql://user:pass@localhost/mydb\nSECRET_KEY=supersecretkey\nDEBUG=true\n```\n\n"
        "```python\n# Python — pip install python-dotenv\nfrom dotenv import load_dotenv\nimport os\n\nload_dotenv()  # reads .env file\n\nDB_URL = os.environ['DATABASE_URL']      # raises if missing\nDEBUG = os.environ.get('DEBUG', 'false') # default value\n```\n\n"
        "```javascript\n// Node.js — npm install dotenv\nrequire('dotenv').config();\nconst dbUrl = process.env.DATABASE_URL;\nconst port = process.env.PORT || 3000;\n```\n\n"
        "**Always add `.env` to `.gitignore`. Use `.env.example` to document what variables are needed.**")

    _s("what is regex", ["regular expressions","regex python","regex javascript","regex tutorial","pattern matching"],
        "**Regex** (regular expressions) match patterns in text.\n\n"
        "```python\nimport re\n\n# Find all emails\ntext = 'Contact alice@example.com or bob@test.org'\nemails = re.findall(r'[\\w.+-]+@[\\w-]+\\.[\\w.]+', text)\n# ['alice@example.com', 'bob@test.org']\n\n# Validate email (simple)\ndef is_email(s): return bool(re.fullmatch(r'[\\w.+-]+@[\\w-]+\\.[\\w.]+', s))\n\n# Replace\nclean = re.sub(r'\\s+', ' ', '  too   many   spaces  ').strip()\n\n# Groups\nm = re.match(r'(\\d{4})-(\\d{2})-(\\d{2})', '2025-01-15')\nif m:\n    year, month, day = m.groups()  # '2025', '01', '15'\n```\n\n"
        "**Common patterns:** `\\d` digit, `\\w` word char, `\\s` whitespace, `.` any char, "
        "`+` one or more, `*` zero or more, `?` optional, `^` start, `$` end, `[abc]` character class.")

    _s("what is websocket", ["websockets","websocket vs http","real time websocket","socket.io"],
        "**WebSockets** — persistent two-way connection between client and server. "
        "Unlike HTTP (request/response), WebSocket keeps the connection open for real-time data.\n\n"
        "**Use for:** chat apps, live notifications, collaborative editing, real-time dashboards, games.\n\n"
        "```javascript\n// Browser\nconst ws = new WebSocket('wss://example.com/socket');\n\nws.onopen    = () => ws.send(JSON.stringify({ type: 'join', room: 'main' }));\nws.onmessage = (e) => console.log(JSON.parse(e.data));\nws.onerror   = (e) => console.error(e);\nws.onclose   = ()  => console.log('Disconnected');\n```\n\n"
        "```python\n# Flask-Sock (Python)\nfrom flask_sock import Sock\nsock = Sock(app)\n\n@sock.route('/ws')\ndef handle(ws):\n    while True:\n        data = ws.receive()\n        ws.send(f'Echo: {data}')\n```")

    _save()


def _seed_vika_faq():
    """VIKA-specific FAQs — never overwrite user answers."""
    _s("how do i use build mode", ["what is build mode","how to build an app"],
        "Click the **Build** tab, then describe what you want:\n\n"
        "> *'Build a to-do list with dark UI and localStorage'*\n\n"
        "VIKA writes the code, the **Preview** tab shows it live, and **ZIP** downloads the whole project.")

    _s("how do i download my project", ["zip download","how to export","download project"],
        "Click the **ZIP** button in the top-right corner — downloads your entire project instantly.")

    _s("how do i connect to github", ["push to github","github token","connect github"],
        "Click the **GitHub icon** in the sidebar → paste your Personal Access Token "
        "(github.com/settings/tokens, `repo` scope) → pick your repo → **Commit & Push**.")

    _s("how do i use the terminal", ["open terminal","terminal help"],
        "Click **>_** in the sidebar or press **Ctrl+`**. Real shell inside your project folder. "
        "Run `node`, `python`, `npm` — anything.")

    _save()


# ─────────────────────────────────────────────────────────────────────────────
# README-based pre-build
# ─────────────────────────────────────────────────────────────────────────────
def prebuild_from_readme(readme: str):
    if not readme:
        return
    lines = [l.strip() for l in readme.split("\n") if l.strip() and not l.startswith("#")]
    summary = " ".join(lines[:10])
    if summary:
        put("tell me about the project", summary[:600], overwrite=False)
        put("what is this project", summary[:600], overwrite=False)
    _save()


def _put_all(primary: str, aliases: list, answer: str):
    put(primary, answer, overwrite=False)
    for a in aliases:
        put(a, answer, overwrite=False)


# ─────────────────────────────────────────────────────────────────────────────
# Bootstrap — load from disk, seed expert Q&A
# ─────────────────────────────────────────────────────────────────────────────
load()
_seed_expert_qa()
_seed_vika_faq()
