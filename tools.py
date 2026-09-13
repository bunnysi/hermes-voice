"""Agent-facing tools for hermes-voice."""

from __future__ import annotations

import json
from typing import Any

try:
    from .config import ConfigError, VoiceConfig, from_mapping, load
    from .fish_client import FishError, end_session, ensure_agent
    from .server import STATE
    from .server import start as start_server
    from .server import stop as stop_server
except ImportError:  # pytest with pythonpath=.
    from config import ConfigError, VoiceConfig, from_mapping, load
    from fish_client import FishError, end_session, ensure_agent
    from server import STATE
    from server import start as start_server
    from server import stop as stop_server

VOICE_CALL_SCHEMA: dict[str, Any] = {
    "name": "voice_call",
    "description": (
        "Start a full-duplex Fish Audio voice call served on a local page. "
        "Returns the URL the user should open. Speech recognition, barge-in, "
        "and TTS run on Fish; replies come from the configured Hermes LLM."
    ),
    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
}

VOICE_STATUS_SCHEMA: dict[str, Any] = {
    "name": "voice_status",
    "description": "Report whether the hermes-voice call page is serving.",
    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
}

VOICE_HANGUP_SCHEMA: dict[str, Any] = {
    "name": "voice_hangup",
    "description": "End the Fish Agents session and stop the local call page.",
    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
}


def _load_cfg() -> VoiceConfig:
    return load()


def handle_voice_call(args: dict, **kwargs) -> str:
    del args, kwargs
    try:
        cfg = _load_cfg()
        snap = start_server(cfg)
        agent_id = ensure_agent(cfg)
        with STATE.lock:
            STATE.agent_id = agent_id
        snap = STATE.snapshot()
        return json.dumps(
            {
                "ok": True,
                "url": snap["url"],
                "agent_id": agent_id,
                "note": "Open the URL and tap call. Allow the microphone.",
            }
        )
    except (ConfigError, FishError, OSError) as exc:
        return json.dumps({"ok": False, "error": str(exc)})


def handle_voice_status(args: dict, **kwargs) -> str:
    del args, kwargs
    snap = STATE.snapshot()
    snap["ok"] = True
    return json.dumps(snap)


def handle_voice_hangup(args: dict, **kwargs) -> str:
    del args, kwargs
    snap = STATE.snapshot()
    session_id = snap.get("session_id")
    if session_id:
        try:
            cfg = _load_cfg()
            end_session(cfg, str(session_id))
        except (ConfigError, FishError):
            pass
    stop_server()
    return json.dumps({"ok": True, "serving": False})


def cfg_from_plugin_settings(settings: dict[str, Any] | None) -> VoiceConfig:
    return from_mapping(settings or {})
