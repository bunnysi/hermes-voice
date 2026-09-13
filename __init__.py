"""hermes-voice plugin — Fish Audio full-duplex calls with a Hermes LLM."""

from __future__ import annotations

import logging

try:
    from .cli import register_cli as _register_cli
    from .cli import voice_command as _voice_command
    from .server import STATE
    from .server import stop as stop_server
    from .tools import (
        VOICE_CALL_SCHEMA,
        VOICE_HANGUP_SCHEMA,
        VOICE_STATUS_SCHEMA,
        handle_voice_call,
        handle_voice_hangup,
        handle_voice_status,
    )
except ImportError:  # pytest with pythonpath=.
    from cli import register_cli as _register_cli
    from cli import voice_command as _voice_command
    from server import STATE
    from server import stop as stop_server
    from tools import (
        VOICE_CALL_SCHEMA,
        VOICE_HANGUP_SCHEMA,
        VOICE_STATUS_SCHEMA,
        handle_voice_call,
        handle_voice_hangup,
        handle_voice_status,
    )

logger = logging.getLogger(__name__)

_TOOLS = (
    ("voice_call", VOICE_CALL_SCHEMA, handle_voice_call, "📞"),
    ("voice_status", VOICE_STATUS_SCHEMA, handle_voice_status, "🟢"),
    ("voice_hangup", VOICE_HANGUP_SCHEMA, handle_voice_hangup, "👋"),
)


def _on_session_end(**kwargs) -> None:
    del kwargs
    try:
        if STATE.snapshot().get("serving"):
            stop_server()
    except Exception as exc:  # pragma: no cover
        logger.debug("hermes-voice session-end cleanup failed: %s", exc)


def register(ctx) -> None:
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="hermes-voice",
            schema=schema,
            handler=handler,
            emoji=emoji,
        )
    ctx.register_cli_command(
        name="voice",
        help="Fish Audio full-duplex voice call",
        setup_fn=_register_cli,
        handler_fn=_voice_command,
        description="Start a local call page backed by Fish Agents + Hermes LLM.",
    )
    ctx.register_hook("on_session_end", _on_session_end)
