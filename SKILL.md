---
name: hermes-voice
description: Start a Fish Audio full-duplex call to Hermes.
version: 0.2.0
author: hareai
license: MIT
metadata:
  hermes:
    tags: [voice, fish, call, duplex]
---

# hermes-voice

Full-duplex voice calls: Fish Audio handles STT, barge-in, and TTS. Replies come from a Hermes OpenAI-compatible API Server (`POST /v1/chat/completions`).

## When to Use

- User wants a live phone call with Hermes
- `voice_call` / `hermes voice call`

## Prerequisites

Copy `config.example.yaml` to `config.yaml` (or `$HERMES_HOME/hermes-voice.yaml`). `llm.base_url` must be **public https** — Fish cannot reach `127.0.0.1`.

## Procedure

1. `hermes plugins install /path/to/hermes-voice` then `hermes plugins enable hermes-voice`
2. Fill `config.yaml`
3. `hermes voice setup`
4. Call `voice_call` or `hermes voice call`
5. Open the printed URL, tap **call**, allow the microphone
6. Hang up with `voice_hangup` or the page button

## Pitfalls

- Loopback LLM URLs fail at Fish session start.
- The page only receives a session token, not the Fish API key.
- Spoken replies stay short. This is a call, not a tool loop.
