"""CLI: hermes voice {setup,call,status,stop}."""

from __future__ import annotations

import argparse
import json
import sys

try:
    from .config import ConfigError, load
    from .fish_client import FishError, ensure_agent
    from .server import STATE
    from .server import start as start_server
    from .server import stop as stop_server
except ImportError:  # pytest with pythonpath=.
    from config import ConfigError, load
    from fish_client import FishError, ensure_agent
    from server import STATE
    from server import start as start_server
    from server import stop as stop_server


def register_cli(subparser: argparse.ArgumentParser) -> None:
    subs = subparser.add_subparsers(dest="voice_command")
    subs.add_parser("setup", help="Validate config.yaml and report LLM/Fish readiness")
    subs.add_parser("call", help="Start the local call page")
    subs.add_parser("status", help="Print serving URL and session id")
    subs.add_parser("stop", help="Stop the local call page")


def voice_command(args: argparse.Namespace) -> int:
    cmd = getattr(args, "voice_command", None)
    if cmd == "setup":
        return _setup()
    if cmd == "call":
        return _call()
    if cmd == "status":
        print(json.dumps(STATE.snapshot(), ensure_ascii=False, indent=2))
        return 0
    if cmd == "stop":
        print(json.dumps(stop_server(), ensure_ascii=False, indent=2))
        return 0
    print("usage: hermes voice {setup,call,status,stop}", file=sys.stderr)
    return 2


def _setup() -> int:
    try:
        cfg = load()
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 1
    print(f"config: {cfg.source_path or '(env only)'}")
    print(f"llm: {cfg.llm_base_url} model={cfg.llm_model}")
    print(f"voice_id: {cfg.voice_id} language={cfg.language}")
    print(f"interruptible: {cfg.interruptible} sensitivity={cfg.interruption_sensitivity}")
    if not cfg.public_https_llm():
        print("warn: llm.base_url should be public https so Fish can reach Hermes", file=sys.stderr)
    return 0


def _call() -> int:
    try:
        cfg = load()
        snap = start_server(cfg)
        agent_id = ensure_agent(cfg)
        with STATE.lock:
            STATE.agent_id = agent_id
        snap = STATE.snapshot()
    except (ConfigError, FishError, OSError) as exc:
        print(f"call failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(snap, ensure_ascii=False, indent=2))
    print(f"open {snap['url']} and tap call")
    return 0
