/* ===================== AI Assistant Unlimited — frontend ===================== */
const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);
const SESSION = "default";
const MONACO_VER = "0.50.0";
const MONACO_BASE = `https://cdn.jsdelivr.net/npm/monaco-editor@${MONACO_VER}/min`;

let mode = "chat";
let model = null;
let busy = false;
let hasFiles = false;

/* ===================== Persistence ===================== */
const STORE = {
  chat: "aiu_chat_v1",
  mode: "aiu_mode_v1",
  settings: "aiu_settings_v1",
};
let transcript = [];
function saveChat(){ try{ localStorage.setItem(STORE.chat, JSON.stringify(transcript)); }catch(e){} }
function loadChat(){ try{ return JSON.parse(localStorage.getItem(STORE.chat)||"[]"); }catch(e){ return []; } }

const defaultSettings = {
  appTheme:"dark", editorTheme:"aiu-midnight", fontSize:13,
  fontFamily:"'JetBrains Mono', monospace", wordWrap:false, minimap:true,
};
let settings = Object.assign({}, defaultSettings);
function loadSettings(){
  try{ settings = Object.assign({}, defaultSettings, JSON.parse(localStorage.getItem(STORE.settings)||"{}")); }
  catch(e){ settings = Object.assign({}, defaultSettings); }
}
function saveSettings(){ try{ localStorage.setItem(STORE.settings, JSON.stringify(settings)); }catch(e){} }

/* ===================== Toast ===================== */
function toast(msg, kind="err"){
  const el = document.createElement("div");
  el.className = "toast " + kind;
  el.innerHTML = `<span class="ti"></span><span class="tt"></span>`;
  el.querySelector(".tt").textContent = msg;
  $("#toasts").appendChild(el);
  setTimeout(()=>{ el.style.opacity="0"; el.style.transition=".3s"; setTimeout(()=>el.remove(),300); }, 4000);
}

/* ===================== Markdown (chat) ===================== */
function escapeHtml(s){return s.replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));}
function renderMarkdown(text){
  let html = escapeHtml(text);
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g,(_,l,c)=>`<pre><code>${c.replace(/\n$/,"")}</code></pre>`);
  html = html.replace(/`([^`]+)`/g,"<code>$1</code>");
  html = html.replace(/\*\*([^*]+)\*\*/g,"<b>$1</b>");
  html = html.split(/\n{2,}/).map(p=>p.trim()?`<p>${p.replace(/\n/g,"<br>")}</p>`:"").join("");
  return html;
}
function renderMsgNode(role, text){
  const wrap = document.createElement("div"); wrap.className="msg-wrap";
  const isAI = role==="ai";
  const msg = document.createElement("div"); msg.className="msg";
  msg.innerHTML = `
    <div class="avatar ${isAI?'ai':'user'}">${isAI?'🤖':'Y'}</div>
    <div style="flex:1;min-width:0">
      <div class="role">${isAI?'Assistant':'You'}</div>
      <div class="bubble">${isAI?renderMarkdown(text):escapeHtml(text).replace(/\n/g,"<br>")}</div>
    </div>`;
  wrap.appendChild(msg);
  return wrap;
}
function addMsg(role, text, persist=true){
  const w = $("#welcome"); if(w) w.remove();
  const node = renderMsgNode(role, text);
  $("#messages").appendChild(node);
  $("#messages").scrollTop = $("#messages").scrollHeight;
  if(persist){ transcript.push({role, text}); saveChat(); }
}
function restoreChat(){
  transcript = loadChat();
  if(transcript.length){
    const w = $("#welcome"); if(w) w.remove();
    transcript.forEach(m => $("#messages").appendChild(renderMsgNode(m.role, m.text)));
    $("#messages").scrollTop = $("#messages").scrollHeight;
  }
}
function addTyping(){
  const wrap = document.createElement("div"); wrap.className="msg-wrap"; wrap.id="typingWrap";
  wrap.innerHTML = `<div class="msg"><div class="avatar ai">🤖</div>
    <div style="flex:1"><div class="role">Assistant</div>
    <div class="typing"><span></span><span></span><span></span></div></div></div>`;
  $("#messages").appendChild(wrap); $("#messages").scrollTop = $("#messages").scrollHeight;
}
function removeTyping(){ const t=$("#typingWrap"); if(t)t.remove(); }

/* ===================== Mode ===================== */
function setMode(m){
  mode = m;
  $("#modeChat").classList.toggle("active", m==="chat");
  $("#modeBuild").classList.toggle("active", m==="build");
  $("#input").placeholder = m==="build" ? "Describe the app you want to build…" : "Ask anything…";
  try{ localStorage.setItem(STORE.mode, m); }catch(e){}
}
$("#modeChat").onclick = ()=>setMode("chat");
$("#modeBuild").onclick = ()=>setMode("build");

/* ===================== Send ===================== */
const input = $("#input"), send = $("#send");
function autosize(){ input.style.height="auto"; input.style.height=Math.min(input.scrollHeight,170)+"px"; }
input.addEventListener("input",()=>{ autosize(); send.disabled = !input.value.trim() || busy; });
input.addEventListener("keydown",e=>{ if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();doSend();} });
send.onclick = doSend;

async function doSend(){
  const text = input.value.trim();
  if(!text || busy) return;
  busy = true; send.disabled = true;
  addMsg("user", text);
  input.value=""; autosize();
  addTyping();
  try{
    if(mode==="build"){ await runBuild(text); } else { await runChat(text); }
  }catch(err){ removeTyping(); toast(err.message || "Something went wrong"); }
  finally{ busy=false; send.disabled = !input.value.trim(); }
}
async function runChat(text){
  const r = await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({message:text, model, session_id:SESSION})});
  const data = await r.json();
  removeTyping();
  if(!r.ok){ toast(data.error||"Request failed"); return; }
  addMsg("ai", data.response);
}
async function runBuild(text){
  setView("preview");
  const r = await fetch("/api/build",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({message:text, model, session_id:SESSION})});
  const data = await r.json();
  removeTyping();
  if(!r.ok){ toast(data.error||"Build failed"); return; }
  const wrote = data.wrote && data.wrote.length ? `\n\n**Updated:** ${data.wrote.join(", ")}` : "";
  addMsg("ai", data.response + wrote);
  await loadFiles();
  if(data.wrote && data.wrote.length){ openFile(data.wrote.includes("index.html")?"index.html":data.wrote[0]); }
  if(data.has_preview){ setView("preview"); reloadPreview(); }
  else { setView("explorer"); }
}

/* ===================== Activity views ===================== */
let activeView = "explorer";
function setView(view){
  activeView = view;
  $$(".act").forEach(a=>a.classList.toggle("active", a.dataset.view===view));
  const isPreview = view==="preview";
  $("#previewView").classList.toggle("hidden", !isPreview);
  $("#editorView").classList.toggle("hidden", isPreview);
  $("#sidebar").classList.toggle("collapsed", isPreview);
  if(!isPreview){
    $("#explorerView").classList.toggle("hidden", view!=="explorer");
    $("#settingsView").classList.toggle("hidden", view!=="settings");
    if(window.__editor) window.__editor.layout();
  }
  if(isPreview) reloadPreview();
}
$$(".act").forEach(a=>{ a.onclick = ()=>setView(a.dataset.view); });

function reloadPreview(){ $("#previewFrame").src = "/preview/?t=" + Date.now(); }
$("#pvRefresh").onclick = reloadPreview;
$("#pvOpen").onclick = ()=>window.open("/preview/","_blank");

/* ===================== Files / Explorer ===================== */
async function loadFiles(){
  const r = await fetch("/api/project/files");
  const data = await r.json();
  hasFiles = data.files.length > 0;
  updateZipBtn();
  const list = $("#fileList"); list.innerHTML="";
  if(!data.files.length){
    list.innerHTML = `<div class="side-empty">No files yet. Switch to <b>Build</b> mode and describe an app, or click <b>+</b> to create a file.</div>`;
    return;
  }
  data.files.forEach(f=>{
    const el = document.createElement("div");
    el.className = "file-item" + (f===activePath?" active":"");
    el.innerHTML = `<svg class="fi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>`;
    const name = document.createElement("span"); name.className="fi-name"; name.textContent=f; el.appendChild(name);
    const del = document.createElement("button"); del.className="fi-del"; del.title="Delete file";
    del.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>`;
    del.onclick = (e)=>{ e.stopPropagation(); deleteFile(f); };
    el.appendChild(del);
    el.onclick = ()=>openFile(f);
    list.appendChild(el);
  });
}
$("#refreshFilesBtn").onclick = loadFiles;
$("#newFileBtn").onclick = async ()=>{
  const name = prompt("New file name (e.g. index.html, css/style.css):");
  if(!name || !name.trim()) return;
  const r = await fetch("/api/project/file",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({path:name.trim(), content:""})});
  if(!r.ok){ toast("Could not create file"); return; }
  await loadFiles();
  openFile(name.trim());
  toast("File created", "ok");
};
async function deleteFile(path){
  if(!confirm(`Delete ${path}? This cannot be undone.`)) return;
  const r = await fetch("/api/project/delete",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({path})});
  if(!r.ok){ toast("Delete failed"); return; }
  closeTab(path, true);
  await loadFiles();
  reloadPreview();
  toast("Deleted", "ok");
}

/* ===================== Editor (Monaco) ===================== */
const tabs = new Map();   // path -> { model, content, dirty }
let activePath = null;
let monacoReady = false;
let fallbackEl = null;    // <textarea> used if Monaco CDN is unreachable

function langForPath(path){
  const ext = (path.split(".").pop()||"").toLowerCase();
  const map = {
    html:"html", htm:"html", css:"css", scss:"scss", less:"less",
    js:"javascript", jsx:"javascript", mjs:"javascript", cjs:"javascript",
    ts:"typescript", tsx:"typescript", json:"json", md:"markdown", markdown:"markdown",
    py:"python", rb:"ruby", go:"go", rs:"rust", java:"java", c:"c", h:"c",
    cpp:"cpp", cc:"cpp", cs:"csharp", php:"php", sh:"shell", bash:"shell",
    yml:"yaml", yaml:"yaml", xml:"xml", sql:"sql", txt:"plaintext", toml:"ini", ini:"ini",
  };
  return map[ext] || "plaintext";
}
function showEditorEmpty(show){
  $("#editorEmpty").classList.toggle("hidden", !show);
  $("#editorHost").style.display = show ? "none" : "block";
  $("#tabbar").style.display = tabs.size ? "flex" : "none";
}
function renderTabs(){
  const bar = $("#tabbar"); bar.innerHTML="";
  tabs.forEach((t, path)=>{
    const tab = document.createElement("div");
    tab.className = "etab" + (path===activePath?" active":"") + (t.dirty?" dirty":"");
    const name = document.createElement("span"); name.className="et-name"; name.textContent = path.split("/").pop();
    name.title = path;
    const dot = document.createElement("span"); dot.className="et-dot";
    const close = document.createElement("button"); close.className="et-close";
    close.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;
    close.onclick = (e)=>{ e.stopPropagation(); closeTab(path); };
    tab.appendChild(name); tab.appendChild(dot); tab.appendChild(close);
    tab.onclick = ()=>activateTab(path);
    bar.appendChild(tab);
  });
  showEditorEmpty(tabs.size===0);
}
function activateTab(path){
  const t = tabs.get(path); if(!t) return;
  activePath = path;
  if(monacoReady && window.__editor){ window.__editor.setModel(t.model); window.__editor.focus(); }
  else if(fallbackEl){ fallbackEl.value = t.content || ""; fallbackEl.focus(); }
  renderTabs();
  updateStatusFile();
  $$("#fileList .file-item").forEach(el=>{
    el.classList.toggle("active", el.querySelector(".fi-name")?.textContent===path);
  });
}
function closeTab(path, silent){
  const t = tabs.get(path);
  if(t){ if(t.model){ try{ t.model.dispose(); }catch(e){} } tabs.delete(path); }
  if(activePath===path){
    const next = tabs.size ? Array.from(tabs.keys())[tabs.size-1] : null;
    activePath = next;
    if(next){ activateTab(next); return; }
    if(monacoReady && window.__editor){ window.__editor.setModel(null); }
    else if(fallbackEl){ fallbackEl.value = ""; }
  }
  renderTabs(); updateStatusFile();
}
async function openFile(path){
  if(tabs.has(path)){ activateTab(path); return; }
  const r = await fetch("/api/project/file?path="+encodeURIComponent(path));
  const data = await r.json();
  if(!r.ok){ toast(data.error||"Could not open file"); return; }
  if(!monacoReady && !fallbackEl){ toast("Editor still loading…"); return; }
  let entry;
  if(monacoReady){
    const model = window.monaco.editor.createModel(data.content, langForPath(path));
    entry = { model, content:data.content, dirty:false };
    model.onDidChangeContent(()=>{
      if(!entry.dirty){ entry.dirty = true; renderTabs(); }
    });
  } else {
    entry = { model:null, content:data.content, dirty:false };
  }
  tabs.set(path, entry);
  activateTab(path);
  if(activeView==="preview") setView("explorer");
}
async function saveCurrent(){
  if(!activePath){ toast("No file open"); return; }
  const t = tabs.get(activePath); if(!t) return;
  const content = (monacoReady && t.model) ? t.model.getValue()
                : (fallbackEl ? fallbackEl.value : (t.content||""));
  t.content = content;
  const r = await fetch("/api/project/file",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({path:activePath, content})});
  if(r.ok){
    t.dirty = false; renderTabs();
    flashSaved();
    reloadPreview();
    if(!hasFiles){ loadFiles(); }
  } else { toast("Save failed"); }
}
function flashSaved(){
  const el = $("#sbSave"); el.textContent = "✓ Saved";
  clearTimeout(window.__saveT);
  window.__saveT = setTimeout(()=>{ el.textContent=""; }, 1800);
}
function updateStatusFile(){
  if(activePath && tabs.has(activePath)){
    $("#sbLang").textContent = langForPath(activePath);
  } else {
    $("#sbLang").textContent = "—";
    $("#sbPos").textContent = "Ln 1, Col 1";
  }
}

/* ===================== Monaco bootstrap ===================== */
function defineThemes(){
  window.monaco.editor.defineTheme("aiu-midnight", {
    base:"vs-dark", inherit:true,
    rules:[
      {token:"comment", foreground:"6b6b76", fontStyle:"italic"},
      {token:"keyword", foreground:"a78bfa"},
      {token:"string", foreground:"7ee787"},
      {token:"number", foreground:"f0b75b"},
      {token:"type", foreground:"7c6cff"},
    ],
    colors:{
      "editor.background":"#1b1b1f",
      "editor.lineHighlightBackground":"#24242b",
      "editorCursor.foreground":"#a78bfa",
      "editorLineNumber.foreground":"#4a4a55",
      "editorLineNumber.activeForeground":"#9a9aa6",
      "editor.selectionBackground":"#3a3360",
      "editorIndentGuide.background":"#2a2a31",
    },
  });
}
function applyEditorSettings(){
  if(!window.__editor) return;
  window.monaco.editor.setTheme(settings.editorTheme);
  window.__editor.updateOptions({
    fontSize: settings.fontSize,
    fontFamily: settings.fontFamily,
    wordWrap: settings.wordWrap ? "on" : "off",
    minimap: { enabled: settings.minimap },
  });
}
function initMonaco(){
  require.config({ paths: { vs: MONACO_BASE + "/vs" } });
  window.MonacoEnvironment = {
    getWorkerUrl: function(){
      return `data:text/javascript;charset=utf-8,${encodeURIComponent(`
        self.MonacoEnvironment = { baseUrl: '${MONACO_BASE}/' };
        importScripts('${MONACO_BASE}/vs/base/worker/workerMain.js');
      `)}`;
    },
  };
  let settled = false;
  const fail = (msg)=>{ if(settled) return; settled = true; enableFallback(msg); };
  // Backstop: if the CDN never responds, fall back so editing still works offline.
  const watchdog = setTimeout(()=>fail("Code editor took too long to load — using a basic editor."), 15000);
  require(["vs/editor/editor.main"], function(){
    if(settled) return; settled = true; clearTimeout(watchdog);
    defineThemes();
    window.__editor = window.monaco.editor.create($("#editorHost"), {
      model: null,
      theme: settings.editorTheme,
      fontSize: settings.fontSize,
      fontFamily: settings.fontFamily,
      wordWrap: settings.wordWrap ? "on" : "off",
      minimap: { enabled: settings.minimap },
      automaticLayout: true,
      scrollBeyondLastLine: false,
      smoothScrolling: true,
      cursorBlinking: "smooth",
      tabSize: 2,
      renderWhitespace: "selection",
      padding: { top: 12 },
    });
    // Ctrl/Cmd+S to save
    window.__editor.addCommand(window.monaco.KeyMod.CtrlCmd | window.monaco.KeyCode.KeyS, saveCurrent);
    window.__editor.onDidChangeCursorPosition(e=>{
      $("#sbPos").textContent = `Ln ${e.position.lineNumber}, Col ${e.position.column}`;
    });
    monacoReady = true;
    showEditorEmpty(true);
  }, function(){ clearTimeout(watchdog); fail("Code editor failed to load (no internet?) — using a basic editor."); });
}
function enableFallback(msg){
  if(fallbackEl) return;
  monacoReady = false;
  const host = $("#editorHost");
  host.innerHTML = "";
  fallbackEl = document.createElement("textarea");
  fallbackEl.className = "fallback-edit";
  fallbackEl.spellcheck = false;
  fallbackEl.setAttribute("aria-label", "Code editor");
  fallbackEl.addEventListener("input", ()=>{
    if(!activePath) return;
    const t = tabs.get(activePath); if(!t) return;
    t.content = fallbackEl.value;
    if(!t.dirty){ t.dirty = true; renderTabs(); }
  });
  fallbackEl.addEventListener("keydown", (e)=>{
    if((e.ctrlKey||e.metaKey) && e.key.toLowerCase()==="s"){ e.preventDefault(); saveCurrent(); }
  });
  host.appendChild(fallbackEl);
  if(msg) toast(msg);
  // Reflect any tab already opened during the loading window.
  if(activePath && tabs.has(activePath)){ fallbackEl.value = tabs.get(activePath).content || ""; }
}

/* ===================== Settings UI ===================== */
function syncSettingsUI(){
  $("#setEditorTheme").value = settings.editorTheme;
  $("#setAppTheme").value = settings.appTheme;
  $("#setFontFamily").value = settings.fontFamily;
  $("#setFontSize").value = settings.fontSize;
  $("#fontSizeVal").textContent = settings.fontSize + "px";
  $("#setWrap").classList.toggle("on", settings.wordWrap);
  $("#setMinimap").classList.toggle("on", settings.minimap);
}
function applyAppTheme(){ $("#app").setAttribute("data-theme", settings.appTheme); }
$("#setEditorTheme").onchange = e=>{ settings.editorTheme=e.target.value; saveSettings(); applyEditorSettings(); };
$("#setAppTheme").onchange = e=>{ settings.appTheme=e.target.value; saveSettings(); applyAppTheme(); };
$("#setFontFamily").onchange = e=>{ settings.fontFamily=e.target.value; saveSettings(); applyEditorSettings(); };
$("#setFontSize").oninput = e=>{ settings.fontSize=+e.target.value; $("#fontSizeVal").textContent=settings.fontSize+"px"; saveSettings(); applyEditorSettings(); };
$("#setWrap").onclick = ()=>{ settings.wordWrap=!settings.wordWrap; $("#setWrap").classList.toggle("on",settings.wordWrap); saveSettings(); applyEditorSettings(); };
$("#setMinimap").onclick = ()=>{ settings.minimap=!settings.minimap; $("#setMinimap").classList.toggle("on",settings.minimap); saveSettings(); applyEditorSettings(); };

/* ===================== ZIP / New ===================== */
function updateZipBtn(){
  const b = $("#downloadBtn");
  b.disabled = !hasFiles;
  b.title = hasFiles ? "Download project as ZIP" : "Build or create files first to enable download";
}
$("#downloadBtn").onclick = ()=>{
  if(!hasFiles){ toast("Nothing to download yet — build or create some files first."); return; }
  window.location = "/api/project/download";
};
$("#newBtn").onclick = async ()=>{
  if(!confirm("Start a new project? This clears the current chat and all files.")) return;
  await fetch("/api/clear",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({session_id:SESSION})});
  await fetch("/api/project/clear",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({session_id:SESSION})});
  transcript = []; saveChat();
  Array.from(tabs.keys()).forEach(p=>closeTab(p, true));
  location.reload();
};

/* ===================== Resizer ===================== */
(function(){
  const sp = $("#vsplit"), chat = $("#chatCol"), wb = $("#workbench");
  let dragging=false;
  sp.addEventListener("mousedown", ()=>{ dragging=true; sp.classList.add("dragging"); document.body.style.userSelect="none"; });
  window.addEventListener("mousemove", e=>{
    if(!dragging) return;
    const rect = wb.getBoundingClientRect();
    let w = e.clientX - rect.left;
    w = Math.max(280, Math.min(rect.width-360, w));
    chat.style.width = w+"px"; chat.style.flex="0 0 "+w+"px";
    if(window.__editor) window.__editor.layout();
  });
  window.addEventListener("mouseup", ()=>{ if(dragging){ dragging=false; sp.classList.remove("dragging"); document.body.style.userSelect=""; if(window.__editor)window.__editor.layout(); } });
})();

/* ===================== Global shortcuts ===================== */
window.addEventListener("keydown", e=>{
  const mod = e.ctrlKey || e.metaKey;
  if(mod && e.key.toLowerCase()==="s"){ e.preventDefault(); if(activePath) saveCurrent(); }
  else if(mod && e.key.toLowerCase()==="b"){ e.preventDefault(); $("#sidebar").classList.toggle("collapsed"); if(window.__editor)window.__editor.layout(); }
  else if(mod && e.shiftKey && e.key.toLowerCase()==="e"){ e.preventDefault(); setView("explorer"); }
});

/* ===================== Chips ===================== */
$$(".chip").forEach(c=>{
  c.onclick = ()=>{ setMode(c.dataset.mode); input.value=c.dataset.prompt; autosize(); send.disabled=false; doSend(); };
});

/* ===================== Status / models ===================== */
async function loadStatus(){
  try{
    const r = await fetch("/api/status"); const d = await r.json();
    const on = d.ollama_running;
    $("#statusDot").className = "dot "+(on?"on":"off");
    $("#modelDot").className = "dot "+(on?"on":"off");
    $("#statusText").textContent = on
      ? `Ollama running${d.web_search?" · web search on":""}`
      : "Ollama offline — run: ollama serve";
    $("#sbModel").textContent = on ? (d.model||"model") : "offline";
    const sel = $("#modelSelect");
    if(d.models && d.models.length){
      sel.innerHTML="";
      d.models.forEach(m=>{ const o=document.createElement("option"); o.value=m; o.textContent=m; sel.appendChild(o); });
      model = d.model && d.models.includes(d.model) ? d.model : d.models[0];
      sel.value = model;
    }else{
      sel.innerHTML = `<option>${d.model||"no models"}</option>`;
      model = d.model;
    }
  }catch(e){
    $("#statusText").textContent = "Cannot reach server";
    $("#statusDot").className="dot off";
    $("#sbModel").textContent = "offline";
  }
}
$("#modelSelect").onchange = e=>{ model = e.target.value; };

/* ===================== Boot ===================== */
loadSettings();
applyAppTheme();
syncSettingsUI();
restoreChat();
try{ setMode(localStorage.getItem(STORE.mode)||"chat"); }catch(e){ setMode("chat"); }
initMonaco();
loadFiles();
setView("explorer");
loadStatus();
setInterval(loadStatus, 15000);
autosize();
