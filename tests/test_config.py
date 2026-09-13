"""VoiceConfig loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from config import ConfigError, from_mapping, load


def test_from_mapping_requires_keys() -> None:
    with pytest.raises(ConfigError, match="fish.api_key"):
        from_mapping({"llm": {"base_url": "https://llm.example/v1", "api_key": "k"}})


def test_rejects_loopback_llm() -> None:
    with pytest.raises(ConfigError, match="public https"):
        from_mapping(
            {
                "fish": {"api_key": "fk"},
                "llm": {"base_url": "http://127.0.0.1:8642/v1", "api_key": "lk"},
            }
        )
    with pytest.raises(ConfigError, match="public https"):
        from_mapping(
            {
                "fish": {"api_key": "fk"},
                "llm": {"base_url": "https://localhost:8642/v1", "api_key": "lk"},
            }
        )


def test_env_overrides_yaml(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FISH_AUDIO_API_KEY", "from-env")
    monkeypatch.setenv("LLM_API_KEY", "llm-env")
    cfg = from_mapping(
        {
            "fish": {"api_key": "yaml-fish", "voice_id": "voice-1", "language": "zh"},
            "llm": {"base_url": "https://llm.example/v1", "api_key": "yaml-llm", "model": "m"},
        }
    )
    assert cfg.fish_api_key == "from-env"
    assert cfg.llm_api_key == "llm-env"
    assert cfg.voice_id == "voice-1"
    assert cfg.interruptible is True


def test_defaults_are_empty_voice_and_english() -> None:
    cfg = from_mapping(
        {
            "fish": {"api_key": "fk"},
            "llm": {"base_url": "https://llm.example/v1", "api_key": "lk"},
        }
    )
    assert cfg.voice_id == ""
    assert cfg.language == "en"
    assert "Hermes" in cfg.system_prompt


def test_load_from_explicit_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FISH_AUDIO_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    path = tmp_path / "config.yaml"
    path.write_text(
        "fish:\n  api_key: file-fish\n  language: zh\n"
        "llm:\n  base_url: https://gw.example/v1\n  api_key: file-llm\n",
        encoding="utf-8",
    )
    cfg = load(str(path))
    assert cfg.fish_api_key == "file-fish"
    assert cfg.llm_base_url == "https://gw.example/v1"
    assert cfg.source_path == str(path)


def test_persist_agent_id(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        "fish:\n  api_key: file-fish\n  language: zh\n  agent_id: \"\"\n"
        "llm:\n  base_url: https://gw.example/v1\n  api_key: file-llm\n",
        encoding="utf-8",
    )
    cfg = load(str(path))
    from config import persist_agent_id

    persist_agent_id(cfg, "ag_saved")
    text = path.read_text(encoding="utf-8")
    assert 'agent_id: "ag_saved"' in text
