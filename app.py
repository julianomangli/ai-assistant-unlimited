import os
import json
import select
import threading

from urllib.parse import urlparse

from flask import Flask, request, jsonify, render_template, send_from_directory, send_file, Response
from flask_sock import Sock
from assistant import AIAssistant, BUILDER_SYSTEM_PROMPT
from config import DEFAULT_MODEL, ENABLE_WEB_SEARCH, ENABLE_VERSION_CHECK
import builder
import terminal as term

app = Flask(__name__)
sock = Sock(app)

# --- Terminal access policy ---------------------------------------------------
# The terminal runs a real shell on the server. That is exactly what you want for
# the free local (in-Replit) use, but on the public deployment it would hand a
# shell to anyone. So: open locally; on the deployed site it is OFF unless the
# owner sets a TERMINAL_PASSWORD secret (then it asks for that password).
#
# Fail closed: we treat the app as "production" if APP_ENV says so OR if any of
# the platform's deployment markers are present. That way, forgetting to set
# APP_ENV on a real deployment does NOT accidentally expose an open shell.
def _is_production() -> bool:
    if os.environ.get("APP_ENV") == "production":
        return True
    for marker in ("REPLIT_DEPLOYMENT", "REPLIT_DEPLOYMENT_ID"):
        if os.environ.get(marker):
            return True
    return False


IS_PROD = _is_production()
TERMINAL_PASSWORD = os.environ.get("TERMINAL_PASSWORD", "")


def terminal_enabled() -> bool:
    return bool(TERMINAL_PASSWORD) or not IS_PROD


def terminal_allowed(pw: str) -> bool:
    if TERMINAL_PASSWORD:
        return pw == TERMINAL_PASSWORD
    return not IS_PROD


def _ws_origin_ok() -> bool:
    """Block cross-site WebSocket hijacking: a browser Origin must match our host.

    Non-browser clients (no Origin header) are allowed through here — for those,
    the password (required in production) remains the real gate.
    """
    origin = request.headers.get("Origin")
    if not origin:
        return True
    try:
        return urlparse(origin).netloc == request.host
    except Exception:
        return False

sessions: dict[str, AIAssistant] = {}
builder_sessions: dict[str, AIAssistant] = {}

BUILD_MAX_TOKENS = 4096


def get_or_create_assistant(session_id: str = "default", model: str = None) -> AIAssistant:
    if session_id not in sessions:
        sessions[session_id] = AIAssistant(model=model or DEFAULT_MODEL)
    elif model and sessions[session_id].model != model:
        sessions[session_id] = AIAssistant(model=model)
    return sessions[session_id]


def get_or_create_builder(session_id: str = "default", model: str = None) -> AIAssistant:
    if session_id not in builder_sessions:
        builder_sessions[session_id] = AIAssistant(
            model=model or DEFAULT_MODEL,
            system_prompt=BUILDER_SYSTEM_PROMPT,
            enable_web_search=False,
        )
    elif model and builder_sessions[session_id].model != model:
        builder_sessions[session_id] = AIAssistant(
            model=model,
            system_prompt=BUILDER_SYSTEM_PROMPT,
            enable_web_search=False,
        )
    return builder_sessions[session_id]


def _ensure_ready(assistant, model):
    """Return an (error_json, status_code) tuple if the AI isn't ready, else None."""
    if not assistant.is_ollama_running():
        return {"error": "The AI engine is starting up. Please wait a moment and try again."}, 503
    available = assistant.get_available_models()
    if not available:
        return {"error": "The AI model is still downloading on the server (happens once after deploy). Please try again in a few minutes."}, 503
    if model and model not in available:
        return {"error": f"The model '{model}' is still downloading. Please try again shortly, or pick an available model."}, 503
    return None


@app.route("/")
def index():
    return render_template("index.html")


# ----------------------------- Chat -----------------------------

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field"}), 400

    message = data["message"].strip()
    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    model = data.get("model") or DEFAULT_MODEL
    enable_web_search = data.get("enable_web_search", ENABLE_WEB_SEARCH)

    session_id = data.get("session_id", "default")
    assistant = get_or_create_assistant(session_id, model)
    assistant.enable_web_search = enable_web_search

    not_ready = _ensure_ready(assistant, model)
    if not_ready:
        return jsonify(not_ready[0]), not_ready[1]

    try:
        response = assistant.chat(message)
        return jsonify({"response": response, "model": assistant.model})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----------------------------- Builder -----------------------------

@app.route("/api/build", methods=["POST"])
def build():
    data = request.get_json(force=True)
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field"}), 400

    message = data["message"].strip()
    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    model = data.get("model") or DEFAULT_MODEL
    session_id = data.get("session_id", "default")
    assistant = get_or_create_builder(session_id, model)

    not_ready = _ensure_ready(assistant, model)
    if not_ready:
        return jsonify(not_ready[0]), not_ready[1]

    try:
        raw = assistant.chat(message, max_tokens=BUILD_MAX_TOKENS)
        files = builder.parse_files(raw)
        if files:
            builder.write_files(files)
        explanation = builder.strip_code(raw) or "Updated your project."
        return jsonify({
            "response": explanation,
            "files": builder.list_files(),
            "wrote": list(files.keys()),
            "has_preview": builder.has_index(),
            "model": assistant.model,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/project/files", methods=["GET"])
def project_files():
    return jsonify({
        "files": builder.list_files(),
        "has_preview": builder.has_index(),
    })


@app.route("/api/project/file", methods=["GET", "POST"])
def project_file():
    if request.method == "GET":
        path = request.args.get("path", "")
        content = builder.read_file(path)
        if content is None:
            return jsonify({"error": "File not found"}), 404
        return jsonify({"path": path, "content": content})

    data = request.get_json(force=True) or {}
    path = data.get("path", "")
    if not path:
        return jsonify({"error": "Missing 'path'"}), 400
    builder.save_file(path, data.get("content", ""))
    return jsonify({"status": "saved", "has_preview": builder.has_index()})


@app.route("/api/project/clear", methods=["POST"])
def project_clear():
    builder.clear_project()
    session_id = (request.get_json(silent=True) or {}).get("session_id", "default")
    if session_id in builder_sessions:
        builder_sessions[session_id].clear_history()
    return jsonify({"status": "cleared"})


@app.route("/api/project/delete", methods=["POST"])
def project_delete():
    data = request.get_json(force=True) or {}
    path = data.get("path", "")
    if not path:
        return jsonify({"error": "Missing 'path'"}), 400
    ok = builder.delete_file(path)
    return jsonify({
        "status": "deleted" if ok else "not_found",
        "files": builder.list_files(),
        "has_preview": builder.has_index(),
    })


@app.route("/api/project/mkdir", methods=["POST"])
def project_mkdir():
    data = request.get_json(force=True) or {}
    path = data.get("path", "")
    if not path:
        return jsonify({"error": "Missing 'path'"}), 400
    builder.make_dir(path)
    return jsonify({"status": "created", "files": builder.list_files()})


@app.route("/api/project/rename", methods=["POST"])
def project_rename():
    data = request.get_json(force=True) or {}
    src = data.get("src", "")
    dst = data.get("dst", "")
    if not src or not dst:
        return jsonify({"error": "Missing 'src' or 'dst'"}), 400
    ok, err = builder.rename_path(src, dst)
    if not ok:
        return jsonify({"error": err or "Rename failed"}), 400
    return jsonify({
        "status": "renamed",
        "files": builder.list_files(),
        "has_preview": builder.has_index(),
    })


@app.route("/api/project/download", methods=["GET"])
def project_download():
    if builder.is_empty():
        return jsonify({
            "error": "Nothing to download yet — build or create some files first."
        }), 400
    buf = builder.make_zip()
    return send_file(
        buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name="project.zip",
    )


# ----------------------------- Live preview -----------------------------

_PREVIEW_EMPTY = """<!doctype html><html><head><meta charset="utf-8">
<style>html,body{height:100%;margin:0;font-family:system-ui,sans-serif;
background:#0a0a0f;color:#6b7280;display:flex;align-items:center;justify-content:center}
.box{text-align:center;opacity:.8}.box h2{color:#9ca3af;font-weight:600}</style></head>
<body><div class="box"><h2>No preview yet</h2>
<p>Switch to Build mode and describe an app to see it live here.</p></div></body></html>"""

# The preview iframe is sandboxed (opaque origin) so generated code can't reach the
# parent app's localStorage or APIs. localStorage/sessionStorage throw in that context,
# so this shim transparently swaps in an in-memory store ONLY when access fails — keeping
# generated apps (e.g. a to-do list) working in the preview without weakening isolation.
_STORAGE_SHIM = """<script>
(function(){function mk(){var s={};return{getItem:function(k){return Object.prototype.hasOwnProperty.call(s,k)?s[k]:null;},setItem:function(k,v){s[k]=String(v);},removeItem:function(k){delete s[k];},clear:function(){s={};},key:function(i){return Object.keys(s)[i]||null;},get length(){return Object.keys(s).length;}};}
try{window.localStorage.getItem("__t");}catch(e){try{Object.defineProperty(window,"localStorage",{value:mk(),configurable:true});}catch(_){}}
try{window.sessionStorage.getItem("__t");}catch(e){try{Object.defineProperty(window,"sessionStorage",{value:mk(),configurable:true});}catch(_){}}})();
</script>"""


def _inject_shim(html: str) -> str:
    lower = html.lower()
    for tag in ("<head", "<html"):
        i = lower.find(tag)
        if i != -1:
            j = html.find(">", i)
            if j != -1:
                return html[: j + 1] + _STORAGE_SHIM + html[j + 1:]
    return _STORAGE_SHIM + html


@app.route("/preview/")
@app.route("/preview/<path:subpath>")
def preview(subpath: str = "index.html"):
    if not subpath:
        subpath = "index.html"
    safe = builder.sanitize_path(subpath)
    import os
    full = os.path.join(builder.PROJECT_DIR, safe)
    if not os.path.isfile(full):
        if safe == "index.html":
            resp = Response(_PREVIEW_EMPTY, mimetype="text/html")
        else:
            return ("Not found", 404)
    elif safe.lower().endswith((".html", ".htm")):
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            resp = Response(_inject_shim(f.read()), mimetype="text/html")
    else:
        resp = send_from_directory(builder.PROJECT_DIR, safe)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp


# ----------------------------- Status -----------------------------

@app.route("/api/status", methods=["GET"])
def status():
    assistant = get_or_create_assistant()
    models = assistant.get_available_models()
    return jsonify({
        "ollama_running": assistant.is_ollama_running(),
        "model": assistant.model,
        "models": models,
        "web_search": ENABLE_WEB_SEARCH,
        "version_check": ENABLE_VERSION_CHECK,
    })


@app.route("/api/clear", methods=["POST"])
def clear():
    session_id = (request.get_json(force=True) or {}).get("session_id", "default")
    if session_id in sessions:
        sessions[session_id].clear_history()
    return jsonify({"status": "cleared"})


@app.route("/api/models", methods=["GET"])
def models():
    assistant = get_or_create_assistant()
    return jsonify({"models": assistant.get_available_models()})


# ----------------------------- Terminal -----------------------------

@app.route("/api/terminal/status", methods=["GET"])
def terminal_status():
    return jsonify({
        "enabled": terminal_enabled(),
        "needs_password": bool(TERMINAL_PASSWORD),
    })


@sock.route("/ws/terminal")
def terminal_ws(ws):
    """Bridge a browser xterm.js terminal to a real bash PTY.

    Protocol — client→server messages are JSON:
      {"auth": "..."}                first message; password (or "" locally)
      {"input": "..."}               keystrokes to write to the shell
      {"resize": {"cols":N,"rows":N}} terminal was resized
    Server→client messages are raw terminal output strings (written to xterm).
    """
    if not _ws_origin_ok():
        try:
            ws.send("\r\n\x1b[1;31m Blocked: cross-site terminal connection refused.\x1b[0m\r\n")
        except Exception:
            pass
        return
    # First message must authenticate.
    try:
        first = ws.receive(timeout=15)
    except Exception:
        return
    pw = ""
    if first:
        try:
            pw = (json.loads(first) or {}).get("auth", "")
        except Exception:
            pw = ""
    if not terminal_allowed(pw):
        msg = (" Terminal is disabled on the live site. Set a TERMINAL_PASSWORD "
               "secret to enable it." if IS_PROD else " Access denied.")
        try:
            ws.send("\r\n\x1b[1;31m" + msg + "\x1b[0m\r\n")
        except Exception:
            pass
        return

    proc, master_fd = term.open_pty_shell(builder.PROJECT_DIR)
    stop = threading.Event()
    send_lock = threading.Lock()

    def pump_output():
        while not stop.is_set():
            try:
                r, _, _ = select.select([master_fd], [], [], 0.2)
                if master_fd in r:
                    data = os.read(master_fd, 4096)
                    if not data:
                        break
                    with send_lock:
                        ws.send(data.decode("utf-8", "replace"))
            except (OSError, ValueError):
                break
            except Exception:
                break
        stop.set()

    reader = threading.Thread(target=pump_output, daemon=True)
    reader.start()

    try:
        while not stop.is_set():
            try:
                msg = ws.receive(timeout=1)
            except Exception:
                break  # connection closed
            if msg is None:
                # Timed out waiting for input; loop again so we notice when the
                # shell has exited (reader thread sets `stop`) and clean up fast.
                if stop.is_set() or not reader.is_alive():
                    break
                continue
            try:
                obj = json.loads(msg)
            except Exception:
                continue
            if "input" in obj:
                try:
                    os.write(master_fd, obj["input"].encode("utf-8"))
                except OSError:
                    break
            elif "resize" in obj:
                rz = obj["resize"] or {}
                term.set_winsize(master_fd, rz.get("rows", 24), rz.get("cols", 80))
    finally:
        stop.set()
        term.terminate(proc, master_fd)


@app.route("/api/github/commit-msg", methods=["POST"])
def github_commit_msg():
    """Ask the AI to write a smart commit message for the current project."""
    try:
        files = builder.list_files()
        if not files:
            return jsonify({"error": "No project files yet."}), 400
        snippets = []
        for path in files[:12]:
            try:
                content = builder.read_file(path)
                snippets.append(f"- {path}: {content[:180].strip()}")
            except Exception:
                snippets.append(f"- {path}")
        summary = "\n".join(snippets)
        prompt = (
            f"Write a concise, professional git commit message (one line, under 72 characters) "
            f"for a web project containing these files:\n\n{summary}\n\n"
            "Return ONLY the commit message text. No quotes, no explanation."
        )
        msg = assistant.chat(prompt, max_tokens=80)
        msg = msg.strip().strip('"').strip("'").split("\n")[0].strip()
        return jsonify({"message": msg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/github/push", methods=["POST"])
def github_push():
    """Push the current project files to a GitHub repository."""
    import requests as req_lib, base64 as b64
    data = request.json or {}
    token      = data.get("token", "").strip()
    owner_repo = data.get("repo", "").strip()
    branch     = data.get("branch", "main").strip() or "main"
    commit_msg = data.get("commit_message", "Update project").strip() or "Update project"
    if not token:
        return jsonify({"error": "No token — please connect first."}), 400
    if not owner_repo or "/" not in owner_repo:
        return jsonify({"error": "Repo must be owner/repo (e.g. julianomangli/my-app)."}), 400
    if builder.is_empty():
        return jsonify({"error": "No project files to push. Build something first!"}), 400
    owner, repo = owner_repo.split("/", 1)
    api  = "https://api.github.com"
    hdrs = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "AI-Assistant-Unlimited",
    }
    def gh(method, url, body=None):
        r = req_lib.request(method, api + url, headers=hdrs, json=body, timeout=30)
        r.raise_for_status()
        return r.json() if r.text else {}
    try:
        user = gh("GET", "/user")
        try:
            gh("GET", f"/repos/{owner}/{repo}")
        except req_lib.HTTPError as e:
            if e.response.status_code == 404:
                gh("POST", "/user/repos", {
                    "name": repo, "description": "Built with AI Assistant Unlimited",
                    "private": False, "auto_init": False,
                })
            else:
                raise
        parent_sha = None
        try:
            ref = gh("GET", f"/repos/{owner}/{repo}/git/ref/heads/{branch}")
            parent_sha = ref["object"]["sha"]
        except req_lib.HTTPError:
            pass
        files = builder.list_files()
        tree_items = []
        for path in files:
            full = os.path.join(builder.PROJECT_DIR, path)
            with open(full, "rb") as f:
                content = f.read()
            blob = gh("POST", f"/repos/{owner}/{repo}/git/blobs", {
                "content": b64.b64encode(content).decode(), "encoding": "base64",
            })
            tree_items.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        tree = gh("POST", f"/repos/{owner}/{repo}/git/trees", {"tree": tree_items})
        commit_body = {
            "message": commit_msg,
            "tree": tree["sha"],
            "author": {
                "name":  user.get("name") or user.get("login", owner),
                "email": user.get("email") or f"{user.get('login', owner)}@users.noreply.github.com",
            },
        }
        if parent_sha:
            commit_body["parents"] = [parent_sha]
        commit = gh("POST", f"/repos/{owner}/{repo}/git/commits", commit_body)
        try:
            gh("PATCH", f"/repos/{owner}/{repo}/git/refs/heads/{branch}", {"sha": commit["sha"]})
        except req_lib.HTTPError:
            gh("POST", f"/repos/{owner}/{repo}/git/refs",
               {"ref": f"refs/heads/{branch}", "sha": commit["sha"]})
        return jsonify({
            "sha": commit["sha"][:7],
            "url": f"https://github.com/{owner}/{repo}/commit/{commit['sha']}",
            "repo_url": f"https://github.com/{owner}/{repo}",
            "files": len(tree_items),
            "user": user.get("login", owner),
        })
    except req_lib.HTTPError as e:
        msg = str(e)
        try: msg = e.response.json().get("message", msg)
        except Exception: pass
        return jsonify({"error": msg}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("🤖 AI Assistant Unlimited")
    print(f"   Model: {DEFAULT_MODEL}")
    print(f"   Web Search: {'Enabled ✅' if ENABLE_WEB_SEARCH else 'Disabled ❌'}")
    print(f"   Version Checking: {'Enabled ✅' if ENABLE_VERSION_CHECK else 'Disabled ❌'}")
    print("   Running at http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
