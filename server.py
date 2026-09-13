"""Local HTTPS-free call page. Session tokens are minted here, never the Fish key."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

try:
    from .config import VoiceConfig
    from .fish_client import FishError, create_session, ensure_agent
except ImportError:  # pytest with pythonpath=.
    from config import VoiceConfig
    from fish_client import FishError, create_session, ensure_agent

CALL_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>hermes-voice</title>
<style>
:root {
  --paper: #14171F;
  --soft: #1B2130;
  --line: #262D3D;
  --t0: #E8E6E1;
  --t3: #A7B0D0;
  --ember: #E08B4F;
  --ember-hot: #F0A36A;
  --serif: Georgia, "Times New Roman", serif;
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
}
* { box-sizing: border-box; margin: 0; }
html, body { height: 100%; }
body {
  min-height: 100dvh;
  background: var(--paper);
  color: var(--t0);
  font-family: var(--serif);
  display: grid;
  place-items: center;
  padding: 1.5rem;
  -webkit-font-smoothing: antialiased;
}
.card {
  width: min(26rem, 100%);
  border: 1px solid var(--line);
  background: var(--soft);
  padding: 1.5rem 1.35rem 1.25rem;
}
.word { color: var(--ember); font-size: 1.8rem; font-weight: 500; }
.meta { margin-top: 0.45rem; font-family: var(--mono); font-size: 0.74rem; letter-spacing: 0.06em; color: var(--t3); }
.status { margin-top: 1.1rem; font-family: var(--mono); font-size: 0.8rem; color: var(--t3); min-height: 1.2em; }
.row { display: flex; gap: 0.6rem; margin-top: 1.2rem; }
button {
  flex: 1;
  min-height: 44px;
  border: 1px solid var(--ember);
  background: transparent;
  color: var(--ember);
  font-family: var(--mono);
  font-size: 0.8rem;
  letter-spacing: 0.06em;
  cursor: pointer;
}
button:hover, button:focus-visible { color: var(--ember-hot); border-color: var(--ember-hot); outline: 2px solid var(--ember-hot); outline-offset: 3px; }
button:disabled { opacity: 0.4; cursor: not-allowed; }
.log { margin-top: 1rem; font-family: var(--mono); font-size: 0.74rem; color: var(--t3); white-space: pre-wrap; min-height: 4rem; }
</style>
</head>
<body>
<main class="card">
  <p class="word">hermes-voice</p>
  <p class="meta">full-duplex · fish.audio</p>
  <p class="status" id="status">idle</p>
  <div class="row">
    <button type="button" id="call">call</button>
    <button type="button" id="hang" disabled>hang up</button>
  </div>
  <p class="log" id="log"></p>
</main>
<script type="module">
import { AgentSession } from "https://cdn.jsdelivr.net/npm/@fishaudio/agent-client@0.2.1/+esm";

const statusEl = document.getElementById("status");
const logEl = document.getElementById("log");
const callBtn = document.getElementById("call");
const hangBtn = document.getElementById("hang");
let session = null;

function setStatus(text) {
  statusEl.textContent = text;
}
function log(line) {
  logEl.textContent = (logEl.textContent ? logEl.textContent + "\\n" : "") + line;
}

async function startCall() {
  callBtn.disabled = true;
  setStatus("connecting");
  const resp = await fetch("/api/session", { method: "POST" });
  const body = await resp.json();
  if (!resp.ok) {
    setStatus("error");
    log(body.error || "session failed");
    callBtn.disabled = false;
    return;
  }
  session = await AgentSession.start({ sessionToken: body.sessionToken });
  hangBtn.disabled = false;
  setStatus("connected");
  session.on("statusChange", (s) => setStatus(s));
  session.on("modeChange", (m) => setStatus(m));
  session.on("userTranscript", ({ text, final }) => { if (final) log("you: " + text); });
  session.on("agentResponse", ({ text }) => log("agent: " + text));
  session.on("disconnect", ({ reason }) => {
    setStatus("ended " + reason);
    hangBtn.disabled = true;
    callBtn.disabled = false;
    session = null;
  });
  session.on("error", (err) => log(String(err.code || err.message || err)));
}

async function hangup() {
  if (session) {
    await session.end();
    session = null;
  }
  hangBtn.disabled = true;
  callBtn.disabled = false;
  setStatus("idle");
}

callBtn.addEventListener("click", () => startCall().catch((e) => {
  setStatus("error");
  log(String(e));
  callBtn.disabled = false;
}));
hangBtn.addEventListener("click", () => hangup());
</script>
</body>
</html>
"""


class CallState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.agent_id: str | None = None
        self.session_id: str | None = None
        self.serving = False
        self.host = "127.0.0.1"
        self.port = 8765

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {
                "serving": self.serving,
                "host": self.host,
                "port": self.port,
                "url": f"http://{self.host}:{self.port}/" if self.serving else None,
                "agent_id": self.agent_id,
                "session_id": self.session_id,
            }


STATE = CallState()
_CFG: VoiceConfig | None = None
_SERVER: ThreadingHTTPServer | None = None
_THREAD: threading.Thread | None = None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _json(self, code: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            raw = CALL_HTML.encode()
            self.send_response(200)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.send_header("content-length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if path == "/api/status":
            self._json(200, STATE.snapshot())
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/session":
            self._json(404, {"error": "not found"})
            return
        cfg = _CFG
        if cfg is None:
            self._json(500, {"error": "plugin not configured"})
            return
        try:
            agent_id = STATE.agent_id or ensure_agent(cfg)
            token = create_session(cfg, agent_id)
        except FishError as exc:
            self._json(502, {"error": str(exc)})
            return
        with STATE.lock:
            STATE.agent_id = agent_id
            STATE.session_id = token.get("session_id")
        self._json(200, {"sessionToken": token, "agent_id": agent_id})


def start(cfg: VoiceConfig) -> dict[str, Any]:
    global _CFG, _SERVER, _THREAD
    _CFG = cfg
    with STATE.lock:
        if STATE.serving and _SERVER is not None:
            return STATE.snapshot()
        STATE.host = cfg.host
        STATE.port = cfg.port
        STATE.serving = True
    server = ThreadingHTTPServer((cfg.host, cfg.port), Handler)
    _SERVER = server
    thread = threading.Thread(target=server.serve_forever, name="hermes-voice-http", daemon=True)
    _THREAD = thread
    thread.start()
    return STATE.snapshot()


def stop() -> dict[str, Any]:
    global _SERVER, _THREAD
    with STATE.lock:
        STATE.serving = False
        STATE.session_id = None
    if _SERVER is not None:
        _SERVER.shutdown()
        _SERVER.server_close()
        _SERVER = None
    _THREAD = None
    return STATE.snapshot()
