# Roadmap

## Phase 1 — Core Platform (this scaffold)
- [x] FastAPI gateway (Govrix) with health check + basic middleware
- [x] FastAPI MemoryMesh with pgvector
- [x] Next.js dashboard shell
- [x] Docker Compose (Postgres+pgvector, Redis, gateway, memory, dashboard)
- [ ] Wire dashboard → gateway → memory end to end
- [ ] vLLM / Ollama integration behind InferCraft stub

## Phase 2 — Memory & Retrieval
- [ ] Qdrant integration alongside pgvector
- [ ] Semantic search endpoint
- [ ] Long-term / episodic memory types
- [ ] Audit logging (TimescaleDB)

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
