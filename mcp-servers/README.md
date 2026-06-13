# MCP Servers

ARIS keeps reviewer/chat/notification bridges under `mcp-servers/`. Some entries are true MCP stdio servers; `feishu-bridge` is an HTTP bridge kept here because it serves the same agent-integration layer.

## Index

| Path | Type | Tools / endpoints | Required env | Status |
|------|------|-------------------|--------------|--------|
| [claude-review/](claude-review/) | MCP reviewer | `review`, `review_reply`, `review_start`, `review_reply_start`, `review_status` | Claude CLI/API auth | Active |
| [codex-review/](codex-review/) | MCP reviewer | `codex`, `codex-reply` | `CODEX_API_KEY` or OpenAI-compatible config | Active |
| [gemini-review/](gemini-review/) | MCP reviewer | `review`, `review_reply`, `review_start`, `review_reply_start`, `review_status` | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Active |
| [llm-chat/](llm-chat/) | MCP chat | `chat` | `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` | Generic fallback |
| [minimax-chat/](minimax-chat/) | MCP chat | `minimax_chat` | `MINIMAX_API_KEY` | Provider fallback |
| [feishu-bridge/](feishu-bridge/) | HTTP bridge | `POST /send`, `GET /poll`, `POST /reply`, `GET /health` | `FEISHU_APP_ID`, `FEISHU_APP_SECRET` | Notification bridge |
| [codex-image2/](codex-image2/) | MCP image bridge | `generate_start`, `generate_status` | local Codex app-server | Experimental |

## Local Checks

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  mcp-servers/claude-review/server.py \
  mcp-servers/codex-review/server.py \
  mcp-servers/codex-review/bridge.py \
  mcp-servers/gemini-review/server.py \
  mcp-servers/codex-image2/server.py
```

Provider smoke tests need live API keys and are intentionally manual.
