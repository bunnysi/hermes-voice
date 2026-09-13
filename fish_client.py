"""Fish Agents REST client. Keys stay on this process; never sent to the browser."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

try:
    from .config import VoiceConfig
except ImportError:  # pytest with pythonpath=.
    from config import VoiceConfig

API = "https://api.fish.audio"


class FishError(RuntimeError):
    """Fish Agents API failure."""


def _request(cfg: VoiceConfig, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Bearer " + cfg.fish_api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "hermes-voice/0.2",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            if not raw:
                return {}
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:800]
        raise FishError(f"Fish {method} {path} HTTP {exc.code}: {detail}") from exc


def _agent_payload(cfg: VoiceConfig) -> dict[str, Any]:
    voice: dict[str, Any] = {"speaking_language": cfg.language}
    if cfg.voice_id:
        voice["voice_id"] = cfg.voice_id
    return {
        "prompt": {
            "system_prompt": cfg.system_prompt,
            "first_message_mode": cfg.first_message_mode,
            "first_message": cfg.first_message,
        },
        "voice": voice,
        "conversation": {
            "interruptible": cfg.interruptible,
            "interruption_sensitivity": cfg.interruption_sensitivity,
            "eagerness": cfg.eagerness,
        },
        "llm": {
            "custom": {
                "base_url": cfg.llm_base_url,
                "model": cfg.llm_model,
                "api_key": cfg.llm_api_key,
            }
        },
    }


def ensure_agent(cfg: VoiceConfig) -> str:
    """Create or reuse a Fish agent whose custom LLM is Hermes."""
    if cfg.agent_id:
        _request(cfg, "PATCH", f"/v1/agent/agents/{cfg.agent_id}/config", _agent_payload(cfg))
        _request(
            cfg,
            "POST",
            f"/v1/agent/agents/{cfg.agent_id}/publish",
            {"title": "hermes-voice", "description": "Hermes custom LLM voice call"},
        )
        return cfg.agent_id
    created = _request(cfg, "POST", "/v1/agent/agents", {"name": cfg.agent_name})
    agent_id = created.get("agent_id")
    if not agent_id:
        raise FishError("Fish create agent returned no agent_id")
    _request(cfg, "PATCH", f"/v1/agent/agents/{agent_id}/config", _agent_payload(cfg))
    _request(
        cfg,
        "POST",
        f"/v1/agent/agents/{agent_id}/publish",
        {"title": "hermes-voice", "description": "Hermes custom LLM voice call"},
    )
    try:
        from .config import persist_agent_id
    except ImportError:  # pytest with pythonpath=.
        from config import persist_agent_id

    persist_agent_id(cfg, str(agent_id))
    return str(agent_id)


def create_session(cfg: VoiceConfig, agent_id: str) -> dict[str, Any]:
    """Mint a Fish Agents session token for the browser SDK."""
    overrides: dict[str, Any] = {
        "language": cfg.language,
        "system_prompt": cfg.system_prompt,
        "first_message": cfg.first_message,
    }
    if cfg.voice_id:
        overrides["voice_id"] = cfg.voice_id
    return _request(
        cfg,
        "POST",
        "/v1/agent/sessions",
        {
            "agent_id": agent_id,
            "timezone": "UTC",
            "world_context": True,
            "overrides": overrides,
        },
    )


def end_session(cfg: VoiceConfig, session_id: str) -> None:
    _request(cfg, "POST", f"/v1/agent/sessions/{session_id}/end", {})
