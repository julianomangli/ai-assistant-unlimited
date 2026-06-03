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
  accent:"#7c6cff",
  lineHeight:1.5, tabSize:2,
  cursorStyle:"line", cursorBlink:"smooth",
  lineNumbers:"on", whitespace:"selection",
  ligatures:false, sticky:true, smooth:true, bracketColors:true,
  indentGuides:true, formatOnSave:false,
  termFontSize:13, termCursor:"block",
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
    const ren = document.createElement("button"); ren.className="fi-act"; ren.title="Rename / move";
    ren.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4z"/></svg>`;
    ren.onclick = (e)=>{ e.stopPropagation(); renameFile(f); };
    el.appendChild(ren);
    const del = document.createElement("button"); del.className="fi-act fi-del"; del.title="Delete file";
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
$("#newFolderBtn").onclick = async ()=>{
  const name = prompt("New folder name (e.g. css, src/components):");
  if(!name || !name.trim()) return;
  const r = await fetch("/api/project/mkdir",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({path:name.trim()})});
  if(!r.ok){ toast("Could not create folder"); return; }
  await loadFiles();
  toast("Folder created", "ok");
};
async function renameFile(path){
  const next = prompt("Rename / move to (new path):", path);
  if(next===null) return;
  const dst = next.trim();
  if(!dst || dst===path) return;
  const r = await fetch("/api/project/rename",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({src:path, dst})});
  const data = await r.json().catch(()=>({}));
  if(!r.ok){ toast(data.error||"Rename failed"); return; }
  // Re-open under the new name if it was open.
  const wasOpen = tabs.has(path);
  if(wasOpen) closeTab(path, true);
  await loadFiles();
  if(wasOpen) openFile(dst);
  reloadPreview();
  toast("Renamed", "ok");
}
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
  if(settings.formatOnSave && monacoReady && window.__editor && t.model){
    try{ await window.__editor.getAction("editor.action.formatDocument")?.run(); }catch(e){}
  }
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
function editorOptions(){
  return {
    fontSize: settings.fontSize,
    fontFamily: settings.fontFamily,
    lineHeight: Math.round(settings.fontSize * settings.lineHeight),
    fontLigatures: settings.ligatures,
    tabSize: settings.tabSize,
    wordWrap: settings.wordWrap ? "on" : "off",
    minimap: { enabled: settings.minimap },
    lineNumbers: settings.lineNumbers,
    renderWhitespace: settings.whitespace,
    cursorStyle: settings.cursorStyle,
    cursorBlinking: settings.cursorBlink,
    smoothScrolling: settings.smooth,
    stickyScroll: { enabled: settings.sticky },
    bracketPairColorization: { enabled: settings.bracketColors },
    guides: { indentation: settings.indentGuides, bracketPairs: settings.bracketColors },
  };
}
function applyEditorSettings(){
  if(!window.__editor) return;
  window.monaco.editor.setTheme(settings.editorTheme);
  window.__editor.updateOptions(editorOptions());
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
    window.__editor = window.monaco.editor.create($("#editorHost"), Object.assign({
      model: null,
      theme: settings.editorTheme,
      automaticLayout: true,
      scrollBeyondLastLine: false,
      padding: { top: 12 },
    }, editorOptions()));
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
function hexToRgb(hex){
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex||"");
  return m ? [parseInt(m[1],16),parseInt(m[2],16),parseInt(m[3],16)] : [124,108,255];
}
function lighten(hex, amt){
  const [r,g,b] = hexToRgb(hex);
  const f = v => Math.round(v + (255-v)*amt);
  return `#${[f(r),f(g),f(b)].map(v=>v.toString(16).padStart(2,"0")).join("")}`;
}
function applyAccent(){
  const a = settings.accent || "#7c6cff";
  const a2 = lighten(a, 0.28);
  const [r,g,b] = hexToRgb(a);
  const root = document.documentElement.style;
  root.setProperty("--accent", a);
  root.setProperty("--accent-2", a2);
  root.setProperty("--accent-grad", `linear-gradient(135deg, ${a}, ${a2})`);
  root.setProperty("--accent-rgb", `${r},${g},${b}`);
  $$("#accentSwatches .swatch[data-accent]").forEach(s=>{
    s.classList.toggle("on", (s.dataset.accent||"").toLowerCase()===a.toLowerCase());
  });
}
const SWITCHES = {
  setWrap:"wordWrap", setMinimap:"minimap", setLigatures:"ligatures",
  setSticky:"sticky", setSmooth:"smooth", setBracket:"bracketColors",
  setGuides:"indentGuides", setFormat:"formatOnSave",
};
function syncSettingsUI(){
  $("#setAppTheme").value = settings.appTheme;
  $("#setEditorTheme").value = settings.editorTheme;
  $("#setFontFamily").value = settings.fontFamily;
  $("#setFontSize").value = settings.fontSize;
  $("#fontSizeVal").textContent = settings.fontSize + "px";
  $("#setLineHeight").value = Math.round(settings.lineHeight*10);
  $("#lineHeightVal").textContent = settings.lineHeight.toFixed(1);
  $("#setTabSize").value = settings.tabSize;
  $("#tabSizeVal").textContent = settings.tabSize;
  $("#setCursorStyle").value = settings.cursorStyle;
  $("#setCursorBlink").value = settings.cursorBlink;
  $("#setLineNumbers").value = settings.lineNumbers;
  $("#setWhitespace").value = settings.whitespace;
  $("#setTermFont").value = settings.termFontSize;
  $("#termFontVal").textContent = settings.termFontSize + "px";
  $("#setTermCursor").value = settings.termCursor;
  $("#setAccentCustom").value = settings.accent;
  for(const [id,key] of Object.entries(SWITCHES)){ $("#"+id).classList.toggle("on", !!settings[key]); }
  applyAccent();
}
function applyAppTheme(){ $("#app").setAttribute("data-theme", settings.appTheme); }

$("#setAppTheme").onchange = e=>{ settings.appTheme=e.target.value; saveSettings(); applyAppTheme(); };
$("#setEditorTheme").onchange = e=>{ settings.editorTheme=e.target.value; saveSettings(); applyEditorSettings(); };
$("#setFontFamily").onchange = e=>{ settings.fontFamily=e.target.value; saveSettings(); applyEditorSettings(); };
$("#setFontSize").oninput = e=>{ settings.fontSize=+e.target.value; $("#fontSizeVal").textContent=settings.fontSize+"px"; saveSettings(); applyEditorSettings(); };
$("#setLineHeight").oninput = e=>{ settings.lineHeight=(+e.target.value)/10; $("#lineHeightVal").textContent=settings.lineHeight.toFixed(1); saveSettings(); applyEditorSettings(); };
$("#setTabSize").oninput = e=>{ settings.tabSize=+e.target.value; $("#tabSizeVal").textContent=settings.tabSize; saveSettings(); applyEditorSettings(); };
$("#setCursorStyle").onchange = e=>{ settings.cursorStyle=e.target.value; saveSettings(); applyEditorSettings(); };
$("#setCursorBlink").onchange = e=>{ settings.cursorBlink=e.target.value; saveSettings(); applyEditorSettings(); };
$("#setLineNumbers").onchange = e=>{ settings.lineNumbers=e.target.value; saveSettings(); applyEditorSettings(); };
$("#setWhitespace").onchange = e=>{ settings.whitespace=e.target.value; saveSettings(); applyEditorSettings(); };
$("#setTermFont").oninput = e=>{ settings.termFontSize=+e.target.value; $("#termFontVal").textContent=settings.termFontSize+"px"; saveSettings(); applyTermSettings(); };
$("#setTermCursor").onchange = e=>{ settings.termCursor=e.target.value; saveSettings(); applyTermSettings(); };
for(const [id,key] of Object.entries(SWITCHES)){
  $("#"+id).onclick = ()=>{ settings[key]=!settings[key]; $("#"+id).classList.toggle("on",settings[key]); saveSettings(); applyEditorSettings(); };
}
$$("#accentSwatches .swatch[data-accent]").forEach(s=>{
  s.onclick = ()=>{ settings.accent=s.dataset.accent; $("#setAccentCustom").value=s.dataset.accent; saveSettings(); applyAccent(); };
});
$("#setAccentCustom").oninput = e=>{ settings.accent=e.target.value; saveSettings(); applyAccent(); };
$("#resetSettings").onclick = ()=>{
  if(!confirm("Reset every setting back to its default?")) return;
  settings = Object.assign({}, defaultSettings);
  saveSettings(); syncSettingsUI(); applyAppTheme(); applyEditorSettings(); applyTermSettings();
  toast("Settings reset", "ok");
};

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

/* ===================== Terminal ===================== */
let term = null, termFit = null, termSocket = null, termOpen = false;
let termInfo = { enabled:true, needs_password:false };
let termConnected = false;

function setTermStatus(text, cls){
  const el = $("#termStatus"); if(!el) return;
  el.textContent = text;
  el.className = "term-status" + (cls?(" "+cls):"");
}
function applyTermSettings(){
  if(!term) return;
  try{
    term.options.fontSize = settings.termFontSize;
    term.options.cursorStyle = settings.termCursor;
    if(termFit) termFit.fit();
    sendResize();
  }catch(e){}
}
function termTheme(){
  const css = getComputedStyle(document.documentElement);
  const dark = settings.appTheme === "dark";
  return {
    background: dark ? "#161619" : "#ffffff",
    foreground: dark ? "#dcdce0" : "#1f2024",
    cursor: (settings.accent || "#7c6cff"),
    selectionBackground: "rgba(124,108,255,.30)",
  };
}
async function fetchTermStatus(){
  try{
    const r = await fetch("/api/terminal/status");
    termInfo = await r.json();
  }catch(e){ termInfo = { enabled:true, needs_password:false }; }
  $("#termToggleAct").classList.toggle("disabled", !termInfo.enabled);
}
function ensureTerm(){
  if(term) return true;
  if(typeof window.Terminal === "undefined"){ toast("Terminal failed to load (no internet?)"); return false; }
  term = new window.Terminal({
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: settings.termFontSize,
    cursorStyle: settings.termCursor,
    cursorBlink: true,
    convertEol: true,
    theme: termTheme(),
  });
  try{
    termFit = new window.FitAddon.FitAddon();
    term.loadAddon(termFit);
  }catch(e){ termFit = null; }
  term.open($("#termHost"));
  term.onData(d=>{ if(termSocket && termSocket.readyState===1) termSocket.send(JSON.stringify({input:d})); });
  try{ if(termFit) termFit.fit(); }catch(e){}
  return true;
}
function sendResize(){
  if(term && termSocket && termSocket.readyState===1){
    termSocket.send(JSON.stringify({resize:{cols:term.cols, rows:term.rows}}));
  }
}
function connectTerm(){
  if(!ensureTerm()) return;
  if(termSocket){ try{ termSocket.close(); }catch(e){} termSocket=null; }
  let pw = "";
  if(termInfo.needs_password){
    pw = prompt("Terminal password:") || "";
  }
  setTermStatus("connecting…");
  const proto = location.protocol === "https:" ? "wss" : "ws";
  termSocket = new WebSocket(`${proto}://${location.host}/ws/terminal`);
  termSocket.onopen = ()=>{
    termConnected = true;
    setTermStatus("connected", "ok");
    termSocket.send(JSON.stringify({auth:pw}));
    setTimeout(()=>{ try{ if(termFit) termFit.fit(); sendResize(); }catch(e){} }, 60);
  };
  termSocket.onmessage = ev=>{ if(term) term.write(ev.data); };
  termSocket.onclose = ()=>{
    termConnected = false;
    setTermStatus("disconnected");
    if(term) term.write("\r\n\x1b[2m[session ended — press the restart icon to start again]\x1b[0m\r\n");
  };
  termSocket.onerror = ()=>{ setTermStatus("error", "err"); };
}
function openTerminal(){
  $("#terminalPanel").classList.add("open");
  $("#termToggleAct").classList.add("active");
  termOpen = true;
  if(window.__editor) window.__editor.layout();
  if(!termConnected) connectTerm();
  setTimeout(()=>{ try{ if(termFit) termFit.fit(); sendResize(); term && term.focus(); }catch(e){} }, 70);
}
function closeTerminal(){
  $("#terminalPanel").classList.remove("open");
  $("#termToggleAct").classList.remove("active");
  termOpen = false;
  if(window.__editor) window.__editor.layout();
}
function toggleTerminal(){
  if(termInfo.enabled===false){ toast("Terminal is turned off on the live site."); return; }
  termOpen ? closeTerminal() : openTerminal();
}
$("#termToggleAct").onclick = toggleTerminal;
$("#termClose").onclick = closeTerminal;
$("#termRestart").onclick = ()=>{ if(term) term.reset(); connectTerm(); };
window.addEventListener("resize", ()=>{ if(termOpen && termFit){ try{ termFit.fit(); sendResize(); }catch(e){} } });

/* Drag-to-resize the terminal panel height */
(function(){
  const handle = $("#termResize"), panel = $("#terminalPanel");
  let dragging=false;
  handle.addEventListener("mousedown", ()=>{ dragging=true; document.body.style.userSelect="none"; });
  window.addEventListener("mousemove", e=>{
    if(!dragging) return;
    const region = panel.parentElement.getBoundingClientRect();
    let h = region.bottom - e.clientY;
    h = Math.max(100, Math.min(region.height-120, h));
    panel.style.height = h+"px";
    if(window.__editor) window.__editor.layout();
    if(termFit){ try{ termFit.fit(); sendResize(); }catch(e){} }
  });
  window.addEventListener("mouseup", ()=>{ if(dragging){ dragging=false; document.body.style.userSelect=""; } });
})();

/* ===================== Global shortcuts ===================== */
window.addEventListener("keydown", e=>{
  const mod = e.ctrlKey || e.metaKey;
  if(e.ctrlKey && e.key==="`"){ e.preventDefault(); toggleTerminal(); }
  else if(mod && e.key.toLowerCase()==="s"){ e.preventDefault(); if(activePath) saveCurrent(); }
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
fetchTermStatus();
autosize();
