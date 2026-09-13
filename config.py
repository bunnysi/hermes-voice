"""Load hermes-voice settings from config.yaml, env, then plugin settings."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

DEFAULT_VOICE_ID = ""
DEFAULT_LANGUAGE = "en"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_MODEL = "hermes-agent"
DEFAULT_AGENT_NAME = "hermes-voice"
DEFAULT_FIRST_MESSAGE = "Hello. I'm here. Speak whenever you're ready."
DEFAULT_SYSTEM_PROMPT = (
    "You are a voice assistant for Hermes. Speak in short spoken sentences. "
    "Do not use markdown, lists, or code. Keep replies to one or two sentences. "
    "This is a phone call: do not call tools and do not invent work you have not done. "
    "If interrupted, stop and wait."
)
EAGERNESS = {"relaxed", "balanced", "eager"}
INTERRUPTION = {"low", "balanced", "high"}
LANGUAGES = {"en", "ja", "zh", "ko", "es", "fr", "de", "pt", "it", "nl"}


class ConfigError(ValueError):
    """Invalid or missing voice-call configuration."""


def _first_env(*names: str) -> str | None:
    for name in names:
        raw = os.getenv(name)
        if raw is None:
            continue
        value = raw.strip()
        if value:
            return value
    return None


def _nested(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def discover_config_path(explicit: str | None = None) -> Path | None:
    if explicit:
        path = Path(explicit).expanduser()
        return path if path.is_file() else None
    env_path = _first_env("HERMES_VOICE_CONFIG")
    if env_path:
        path = Path(env_path).expanduser()
        return path if path.is_file() else None
    here = Path.cwd() / "config.yaml"
    if here.is_file():
        return here
    plugin = Path(__file__).resolve().parent / "config.yaml"
    if plugin.is_file():
        return plugin
    home = os.getenv("HERMES_HOME")
    if home:
        path = Path(home) / "hermes-voice.yaml"
        if path.is_file():
            return path
    return None


def load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise ConfigError("PyYAML is required to read config.yaml")
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError("config.yaml must be a mapping")
    return data


def _str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip() or default


def _bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def _int(value: Any, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError("call.port must be an integer") from exc


@dataclass(frozen=True)
class VoiceConfig:
    fish_api_key: str
    voice_id: str
    language: str
    interruptible: bool
    interruption_sensitivity: str
    eagerness: str
    agent_id: str
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    agent_name: str
    first_message_mode: str
    first_message: str
    system_prompt: str
    host: str
    port: int
    source_path: str | None

    def public_https_llm(self) -> bool:
        url = self.llm_base_url
        return url.startswith("https://") and "127.0.0.1" not in url and "localhost" not in url


def from_mapping(
    data: dict[str, Any] | None = None, *, source_path: str | None = None
) -> VoiceConfig:
    data = data or {}
    language = _first_env("FISH_LANGUAGE") or _str(
        _nested(data, "fish", "language"), DEFAULT_LANGUAGE
    )
    if language not in LANGUAGES:
        raise ConfigError(f"fish.language must be one of {sorted(LANGUAGES)}")
    eagerness = _str(_nested(data, "fish", "eagerness"), "balanced")
    if eagerness not in EAGERNESS:
        raise ConfigError("fish.eagerness must be relaxed, balanced, or eager")
    sensitivity = _str(_nested(data, "fish", "interruption_sensitivity"), "high")
    if sensitivity not in INTERRUPTION:
        raise ConfigError("fish.interruption_sensitivity must be low, balanced, or high")
    mode = _str(_nested(data, "agent", "first_message_mode"), "fixed")
    if mode not in {"off", "fixed", "prompt"}:
        raise ConfigError("agent.first_message_mode must be off, fixed, or prompt")

    llm_base = (
        _first_env("LLM_BASE_URL")
        or _str(_nested(data, "llm", "base_url"))
    ).rstrip("/")
    fish_key = _first_env("FISH_AUDIO_API_KEY", "FISH_API_KEY") or _str(
        _nested(data, "fish", "api_key")
    )
    llm_key = _first_env("LLM_API_KEY", "API_SERVER_KEY", "HERMES_API_KEY") or _str(
        _nested(data, "llm", "api_key")
    )
    if not fish_key:
        raise ConfigError("fish.api_key (or FISH_AUDIO_API_KEY) is required")
    if not llm_base:
        raise ConfigError("llm.base_url (or LLM_BASE_URL) is required")
    if not llm_key:
        raise ConfigError("llm.api_key (or LLM_API_KEY) is required")
    if not llm_base.startswith("https://"):
        raise ConfigError("llm.base_url must be public https; Fish Agents cannot reach loopback")
    lowered = llm_base.lower()
    if any(host in lowered for host in ("127.0.0.1", "localhost", "0.0.0.0", "[::1]")):
        raise ConfigError("llm.base_url must be public https; Fish Agents cannot reach loopback")

    return VoiceConfig(
        fish_api_key=fish_key,
        voice_id=_first_env("FISH_VOICE_ID", "FISH_REFERENCE_ID")
        or _str(_nested(data, "fish", "voice_id"), DEFAULT_VOICE_ID),
        language=language,
        interruptible=_bool(_nested(data, "fish", "interruptible"), True),
        interruption_sensitivity=sensitivity,
        eagerness=eagerness,
        agent_id=_first_env("FISH_AGENT_ID") or _str(_nested(data, "fish", "agent_id")),
        llm_base_url=llm_base,
        llm_api_key=llm_key,
        llm_model=_first_env("LLM_MODEL") or _str(_nested(data, "llm", "model"), DEFAULT_MODEL),
        agent_name=_str(_nested(data, "agent", "name"), DEFAULT_AGENT_NAME),
        first_message_mode=mode,
        first_message=_str(_nested(data, "agent", "first_message"), DEFAULT_FIRST_MESSAGE),
        system_prompt=_str(_nested(data, "agent", "system_prompt"), DEFAULT_SYSTEM_PROMPT),
        host=_first_env("VOICE_HOST") or _str(_nested(data, "call", "host"), DEFAULT_HOST),
        port=_int(_first_env("VOICE_PORT") or _nested(data, "call", "port"), DEFAULT_PORT),
        source_path=source_path,
    )


def load(explicit: str | None = None) -> VoiceConfig:
    path = discover_config_path(explicit)
    data = load_yaml(path) if path else {}
    return from_mapping(data, source_path=str(path) if path else None)


def persist_agent_id(cfg: VoiceConfig, agent_id: str) -> None:
    """Write fish.agent_id back to config.yaml after first create."""
    if not agent_id or not cfg.source_path:
        return
    path = Path(cfg.source_path)
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if "agent_id:" not in text:
        if not text.endswith("\n"):
            text += "\n"
        path.write_text(text + f'  agent_id: "{agent_id}"\n', encoding="utf-8")
        return
    updated, n = re.subn(
        r"(agent_id:\s*)([\"']?)([^\"'\n]*)\2",
        rf'\1"{agent_id}"',
        text,
        count=1,
    )
    if n:
        path.write_text(updated, encoding="utf-8")
