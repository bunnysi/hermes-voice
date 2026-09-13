"""Isolate host Fish/LLM env from unit tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _clear_voice_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "FISH_AUDIO_API_KEY",
        "FISH_API_KEY",
        "FISH_VOICE_ID",
        "FISH_REFERENCE_ID",
        "FISH_AGENT_ID",
        "FISH_LANGUAGE",
        "LLM_BASE_URL",
        "LLM_API_KEY",
        "API_SERVER_KEY",
        "HERMES_API_KEY",
        "LLM_MODEL",
        "VOICE_HOST",
        "VOICE_PORT",
        "HERMES_VOICE_CONFIG",
    ):
        monkeypatch.delenv(name, raising=False)
