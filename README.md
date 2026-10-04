# hermes-voice

Hermes plugin for full-duplex Fish Audio voice calls.

[简体中文](README.zh-CN.md)

## Quick start

```bash
git clone https://github.com/hipness/hermes-voice.git
cd hermes-voice
cp config.example.yaml config.yaml
# fill fish.api_key, llm.base_url, llm.api_key
hermes plugins install .
hermes plugins enable hermes-voice
hermes voice setup
hermes voice call
```

Open the printed URL, tap **call**, allow the microphone.

Python 3.11+. `llm.base_url` must be public `https` — Fish cannot reach `127.0.0.1`.

## Usage

Copy `config.example.yaml` to `config.yaml`, or write the same keys under `plugins.entries.hermes-voice.settings` in Hermes `config.yaml`. Environment variables override the file.

| Purpose | YAML | Env |
|---|---|---|
| Fish key | `fish.api_key` | `FISH_AUDIO_API_KEY` |
| Voice id | `fish.voice_id` | `FISH_VOICE_ID` |
| Hermes LLM | `llm.base_url` / `llm.api_key` / `llm.model` | `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` |

Tools: `voice_call`, `voice_status`, `voice_hangup`. CLI: `hermes voice {setup,call,status,stop}`.

```bash
uv sync --extra dev
uv run ruff check .
uv run pytest
```

## License

[MIT](LICENSE)
