"""Local call page mints a session token without exposing the Fish key."""

from __future__ import annotations

import json
from urllib.request import Request, urlopen

import pytest

import fish_client
import server as server_mod
from config import from_mapping
from server import start, stop


def _cfg(port: int):
    return from_mapping(
        {
            "fish": {"api_key": "secret-fish-key", "language": "zh"},
            "llm": {"base_url": "https://gw.example/v1", "api_key": "lk"},
            "call": {"host": "127.0.0.1", "port": port},
        }
    )


def test_session_endpoint_hides_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        fish_client,
        "ensure_agent",
        lambda cfg: "ag_test",
    )
    monkeypatch.setattr(
        fish_client,
        "create_session",
        lambda cfg, agent_id: {
            "session_id": "sess",
            "expires_at": "2099-01-01T00:00:00Z",
            "max_duration_seconds": 60,
            "transport": "livekit",
            "livekit_url": "wss://lk",
            "token": "jwt-token",
        },
    )
    monkeypatch.setattr(server_mod, "ensure_agent", fish_client.ensure_agent)
    monkeypatch.setattr(server_mod, "create_session", fish_client.create_session)
    cfg = _cfg(18765)
    start(cfg)
    try:
        req = Request("http://127.0.0.1:18765/api/session", method="POST", data=b"")
        with urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read())
        assert body["sessionToken"]["token"] == "jwt-token"
        dumped = json.dumps(body)
        assert "secret-fish-key" not in dumped
        with urlopen("http://127.0.0.1:18765/", timeout=5) as page:
            html = page.read().decode()
        assert "secret-fish-key" not in html
        assert "AgentSession" in html
        assert "call" in html
    finally:
        stop()
