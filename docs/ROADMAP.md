# Roadmap

## Phase 1 — Core Platform (this scaffold)
- [x] FastAPI gateway (Govrix) with health check, auth, rate limiting, policy enforcement, audit logging, CORS
- [x] FastAPI MemoryMesh — store/list/search endpoints, SQLite-backed (see note below)
- [x] Next.js + Tailwind dashboard shell
- [x] Native run path (no Docker/WSL required) — verified end-to-end locally
- [x] Docker Compose as an alternative path (Redis, gateway, memory, dashboard)
- [x] Wire dashboard → gateway end to end (health check over CORS)
- [x] Wire gateway `/v1/prompt` → MemoryMesh retrieval → InferCraft → response, storing the exchange back
- [x] InferCraft routing to OpenAI / Anthropic / Ollama when configured, falls back to a labeled stub with zero config
- [x] Dashboard UI for sending prompts and viewing responses (agent console + live memory panel)
- [x] Verified live with a real local model (Ollama `llama3.2:1b`) — full loop confirmed: prompt → memory retrieval → inference → response → memory storage

## Phase 2 — Memory & Retrieval
- [x] Real embedding model — Ollama `all-minilm` (384-dim), replacing the Phase 1 hashing approximation. Falls back to the hash embedding if Ollama is unreachable so the service degrades instead of failing outright.
- [x] Qdrant integration — swapped SQLite's brute-force cosine scan for `qdrant-client`'s embedded/local mode (no server, no Docker; data lives in `memory/qdrant_data/`). MemoryMesh no longer has a SQL database at all.
- [x] Working / episodic / semantic / long_term memory types now have real behavior: `working` expires after 60 minutes and is pruned lazily on read; `episodic` gets an exponentially-decaying recency boost in search ranking; `semantic`/`long_term` are stable regardless of age. See `memory/app/kinds.py`.
- [x] Audit logging persisted to SQLite (`gateway/audit.db`) via `gateway/app/audit.py`, queryable at `GET /v1/audit`. Console logging kept alongside.

> **Storage note:** MemoryMesh's Qdrant runs in **embedded/local mode** — it's a
> Python-in-process index backed by a local directory, not a server. This keeps
> the native (no-Docker) run path intact. Local mode file-locks its data
> directory, so only one MemoryMesh process can run against it at a time.

## Phase 3 — Multi-Agent System
- [ ] Agent registry + task orchestration
- [ ] Tool execution framework
- [ ] InferCraft model routing (small/large/reasoning split)

## Phase 4 — Skill Management
- [ ] Skill registry + versioning
- [ ] Human approval workflow
- [ ] Skill suggestion (manual, not auto-mined)

## Phase 5 — Observability
- [ ] Prometheus + Grafana
- [ ] OpenTelemetry tracing
- [ ] RAGAS eval harness
- [ ] Locust load tests

## Phase 6 — Improvement Engine
- [ ] EvolveCraft metrics collection (MAPE-K: Monitor/Analyze)
- [ ] Diff generation for proposed changes (Plan)
- [ ] Human approval UI (never auto-applies changes)
- [ ] Versioned deployment (Execute/Knowledge)
