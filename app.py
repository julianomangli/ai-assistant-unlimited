from flask import Flask, request, jsonify, render_template, send_from_directory, send_file, Response
from assistant import AIAssistant, BUILDER_SYSTEM_PROMPT
from config import DEFAULT_MODEL, ENABLE_WEB_SEARCH, ENABLE_VERSION_CHECK
import builder

app = Flask(__name__)

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


if __name__ == "__main__":
    print("🤖 AI Assistant Unlimited")
    print(f"   Model: {DEFAULT_MODEL}")
    print(f"   Web Search: {'Enabled ✅' if ENABLE_WEB_SEARCH else 'Disabled ❌'}")
    print(f"   Version Checking: {'Enabled ✅' if ENABLE_VERSION_CHECK else 'Disabled ❌'}")
    print("   Running at http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
