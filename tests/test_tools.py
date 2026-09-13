"""Tool handlers return JSON and never raise."""

from __future__ import annotations

import json

import pytest

import tools
from config import ConfigError


def test_voice_call_reports_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom() -> None:
        raise ConfigError("missing key")

    monkeypatch.setattr(tools, "_load_cfg", _boom)
    out = json.loads(tools.handle_voice_call({}))
    assert out["ok"] is False
    assert "missing key" in out["error"]


def test_voice_status_ok() -> None:
    out = json.loads(tools.handle_voice_status({}))
    assert out["ok"] is True
    assert "serving" in out
