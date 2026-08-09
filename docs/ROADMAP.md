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

> **Storage note:** MemoryMesh uses SQLite + a zero-dependency hashing embedding
> instead of Postgres/pgvector/Qdrant + a real embedding model. This was a deliberate
> tradeoff to avoid requiring WSL/Docker/native build tools for local dev. The
> store/list/search interface matches what a real vector-DB implementation would
> expose, so swapping it in (Phase 2) shouldn't require changes above MemoryMesh.

## Phase 2 — Memory & Retrieval
- [ ] Real embedding model (sentence-transformers or an API-based embedding)
- [ ] Qdrant or pgvector integration (swap out SQLite brute-force search)
- [ ] Long-term / episodic memory types (currently only a single `kind` field, unused by callers)
- [ ] Audit logging persisted to a database (currently stdout only, see `gateway/app/audit.py`)

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
