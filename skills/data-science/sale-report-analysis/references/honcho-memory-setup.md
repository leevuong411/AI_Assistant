# Honcho Self-Hosted Memory — Setup & Integration

## Architecture on ops-aiapp01

Honcho runs as 4 Docker containers:
- `honcho-api-1` — API server on port 8000
- `honcho-deriver-1` — dialectic/deriver worker
- `honcho-database-1` — pgvector/pgvector:pg15 (port 5432)
- `honcho-redis-1` — redis:8.2 cache

### Embedding
- Model: **bge-m3** (1024 dimensions)
- Served via local vLLM/Ollama at `http://host.docker.internal:11434/v1`

### Dialectic models
- `qwen2.5:3b` for dream induction/deduction
- Also served via local Ollama

## Hermes ↔ Honcho Config

### Config files
- Hermes config: `~/.hermes/config.yaml` → `memory.provider: honcho`
- Honcho config: `~/.hermes/honcho.json` → `baseUrl: http://localhost:8000`

### Enable steps
```bash
# 1. Set provider
hermes config set memory.provider honcho
hermes config set memory.memory_enabled true
hermes config set memory.user_profile_enabled true

# 2. Enable Honcho
hermes honcho enable

# 3. Restart from separate SSH (NOT from bot terminal)
hermes gateway restart
```

### Verify
```bash
hermes honcho status
```
Should show: Host=hermes, Enabled=True, Connection=OK

## Honcho API (v3)

Base: `http://localhost:8000/v3/`

Key endpoints:
- `/v3/workspaces` — create/list workspaces
- `/v3/workspaces/{id}/peers/list` — list peers
- `/v3/workspaces/{id}/peers/{id}/chat` — dialectic chat
- `/v3/workspaces/{id}/peers/{id}/context` — get context
- `/v3/workspaces/{id}/search` — semantic search
- `/v3/workspaces/{id}/sessions/list` — list sessions

## Honcho CLI Commands
```bash
hermes honcho status          # Connection + config status
hermes honcho peers           # Show peer identities
hermes honcho sessions        # List session mappings
hermes honcho mode            # Show/set recall mode (hybrid/context/tools)
hermes honcho strategy        # Session strategy (per-session/global)
hermes honcho tokens          # Token budget
hermes honcho identity        # Seed AI peer identity
hermes honcho enable/disable  # Toggle per profile
hermes honcho sync            # Sync config to all profiles
```

## Hermes Memory: Built-in vs Honcho

| Feature | Built-in (file) | Honcho |
|---|---|---|
| Type | Key-value, 2200 char limit | Vector DB, unlimited |
| Semantic search | ❌ | ✅ bge-m3 |
| Cross-session | Per-session file | ✅ Persistent |
| Dialectic Q&A | ❌ | ✅ |
| Peer cards | ❌ | ✅ |
| Setup | Zero config | Docker + config |

## Pitfalls
1. `hermes config set` writes config but requires gateway restart to take effect — and cannot restart from inside the gateway (bot terminal). Must use separate SSH.
2. `honcho: {}` in config.yaml means Honcho block is empty — not configured. The actual config lives in `~/.hermes/honcho.json`.
3. Both memory systems can coexist: Hermes built-in memory tool writes to file-based store; Honcho provides semantic recall. Setting `memory.provider: honcho` routes the memory toolset through Honcho.
