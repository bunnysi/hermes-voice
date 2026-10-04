# hermes-voice

Hermes 插件：全双工 Fish Audio 语音电话。

[English](README.md)

## 快速开始

```bash
git clone https://github.com/hipness/hermes-voice.git
cd hermes-voice
cp config.example.yaml config.yaml
# 填写 fish.api_key、llm.base_url、llm.api_key
hermes plugins install .
hermes plugins enable hermes-voice
hermes voice setup
hermes voice call
```

打开打印出的地址，点 **call**，允许麦克风。

需要 Python 3.11+。`llm.base_url` 必须是公网 `https`，Fish 访问不到本机回环地址。

## 用法

把 `config.example.yaml` 复制为 `config.yaml`，或把同一组键写在 Hermes `config.yaml` 的 `plugins.entries.hermes-voice.settings`。环境变量覆盖文件。

| 用途 | YAML | 环境变量 |
|---|---|---|
| Fish 密钥 | `fish.api_key` | `FISH_AUDIO_API_KEY` |
| 音色 | `fish.voice_id` | `FISH_VOICE_ID` |
| Hermes LLM | `llm.base_url` / `llm.api_key` / `llm.model` | `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` |

工具：`voice_call`、`voice_status`、`voice_hangup`。命令：`hermes voice {setup,call,status,stop}`。

```bash
uv sync --extra dev
uv run ruff check .
uv run pytest
```

## 许可证

[MIT](LICENSE)
