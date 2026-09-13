"""Fish Agents client with a fake HTTP backend."""

from __future__ import annotations

from typing import Any

import pytest

from config import from_mapping
from fish_client import FishError, create_session, ensure_agent


class FakeHTTP:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []
        self.responses: dict[tuple[str, str], Any] = {}

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import fish_client

        def _request(cfg, method, path, body=None):  # noqa: ANN001
            self.calls.append((method, path, body))
            key = (method, path)
            if key not in self.responses:
                raise FishError(f"unexpected {method} {path}")
            item = self.responses[key]
            if isinstance(item, Exception):
                raise item
            return item

        monkeypatch.setattr(fish_client, "_request", _request)


def _cfg():
    return from_mapping(
        {
            "fish": {"api_key": "fk", "voice_id": "vid", "language": "zh"},
            "llm": {"base_url": "https://gw.example/v1", "api_key": "lk", "model": "hermes-agent"},
        }
    )


def test_ensure_agent_creates_and_publishes(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    fake = FakeHTTP()
    fake.responses[("POST", "/v1/agent/agents")] = {"agent_id": "ag_1"}
    fake.responses[("PATCH", "/v1/agent/agents/ag_1/config")] = {}
    fake.responses[("POST", "/v1/agent/agents/ag_1/publish")] = {"version_number": 1}
    fake.install(monkeypatch)
    path = tmp_path / "config.yaml"
    path.write_text(
        "fish:\n  api_key: fk\n  language: zh\n  voice_id: vid\n  agent_id: \"\"\n"
        "llm:\n  base_url: https://gw.example/v1\n  api_key: lk\n  model: hermes-agent\n",
        encoding="utf-8",
    )
    from config import load

    cfg = load(str(path))
    assert ensure_agent(cfg) == "ag_1"
    methods = [c[0] + " " + c[1] for c in fake.calls]
    assert methods == [
        "POST /v1/agent/agents",
        "PATCH /v1/agent/agents/ag_1/config",
        "POST /v1/agent/agents/ag_1/publish",
    ]
    patch_body = fake.calls[1][2] or {}
    assert patch_body["llm"]["custom"]["base_url"] == "https://gw.example/v1"
    assert patch_body["voice"]["voice_id"] == "vid"
    assert 'agent_id: "ag_1"' in path.read_text(encoding="utf-8")


def test_ensure_agent_reuses_id(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeHTTP()
    fake.responses[("PATCH", "/v1/agent/agents/kept/config")] = {}
    fake.responses[("POST", "/v1/agent/agents/kept/publish")] = {"version_number": 2}
    fake.install(monkeypatch)
    data = {
        "fish": {"api_key": "fk", "agent_id": "kept", "language": "zh"},
        "llm": {"base_url": "https://gw.example/v1", "api_key": "lk"},
    }
    assert ensure_agent(from_mapping(data)) == "kept"
    assert fake.calls[0][0] == "PATCH"


def test_create_session_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeHTTP()
    fake.responses[("POST", "/v1/agent/sessions")] = {
        "session_id": "s1",
        "expires_at": "2099-01-01T00:00:00Z",
        "max_duration_seconds": 1800,
        "transport": "livekit",
        "livekit_url": "wss://example",
        "token": "jwt",
    }
    fake.install(monkeypatch)
    token = create_session(_cfg(), "ag_1")
    assert token["transport"] == "livekit"
    assert token["token"] == "jwt"
    body = fake.calls[0][2] or {}
    assert body["agent_id"] == "ag_1"
    assert body["timezone"] == "UTC"
    assert body["overrides"]["language"] == "zh"
    assert body["overrides"]["voice_id"] == "vid"


def test_empty_voice_id_omitted(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeHTTP()
    fake.responses[("PATCH", "/v1/agent/agents/kept/config")] = {}
    fake.responses[("POST", "/v1/agent/agents/kept/publish")] = {"version_number": 2}
    fake.install(monkeypatch)
    data = {
        "fish": {"api_key": "fk", "agent_id": "kept", "language": "en"},
        "llm": {"base_url": "https://gw.example/v1", "api_key": "lk"},
    }
    ensure_agent(from_mapping(data))
    patch_body = fake.calls[0][2] or {}
    assert "voice_id" not in patch_body["voice"]
    assert patch_body["voice"]["speaking_language"] == "en"
