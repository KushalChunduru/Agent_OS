# Architecture

Full target design (most layers beyond Phase 1 are not yet implemented — see [ROADMAP.md](ROADMAP.md)):

```
USER
  │
  ▼
L0 Dashboard Console       (Next.js, agent mgmt, live monitoring, skill marketplace, audit viewer)
  │
  ▼
L1 Govrix Scout            (governance & security: prompt validation, tool permissions,
  │                          cost limits, auth, rate limiting, policy enforcement, audit log)
  ├──────────────┬──────────────┐
  ▼              ▼              ▼
L2A MemoryMesh  L2B InferCraft  L2C SkillForge
(persistent      (model/prompt   (mines repeated workflows
 memory: Qdrant,  routing, GPU   into reusable skills —
 pgvector)        scheduling)    design concept, not shipped)
  │
  ▼
L2E EvolveCraft             (self-improvement loop, MAPE-K:
  │                          Monitor → Analyze → Plan → Execute → Knowledge.
  │                          Never auto-applies changes — generates a diff,
  │                          waits for human approval.)
  ▼
L3 Storage Layer            (TimescaleDB, pgvector, Qdrant, Redis, Neo4j, ScyllaDB —
  │                          specialized store per workload, independently tunable)
  ▼
L4 Observability            (Prometheus, Grafana, RAGAS, Locust)
```

## Why layered instead of monolithic

A single database and a single service handling governance, memory, inference, and
monitoring becomes a bottleneck and a single point of failure. Splitting each concern
into its own service means:

- Independent scaling and tuning per workload (vector search vs. time-series vs. cache)
- Nothing can bypass governance — Govrix sits in front of every LLM call
- Storage backends can be swapped without touching the services above them

## What's actually implemented today

**Dashboard**, **Govrix**, **MemoryMesh**, and a minimal **InferCraft** all exist as
running code and work end-to-end natively (no Docker required):

- MemoryMesh uses **Qdrant in embedded/local mode** (in-process, backed by a local
  directory — no server, no Docker) for vector search, and **Ollama (`all-minilm`)**
  for real embeddings, falling back to a hashing approximation if Ollama is
  unreachable. Memory kinds (`working`/`episodic`/`semantic`/`long_term`) have real
  behavior: working memory expires, episodic gets a recency boost in ranking.
- Govrix's `/v1/prompt` route runs auth → rate-limit → policy → MemoryMesh retrieval
  → InferCraft (routes to Anthropic/OpenAI/Ollama, whichever is configured, else a
  labeled stub) → stores the exchange back into memory. Audit decisions persist to
  SQLite, queryable at `GET /v1/audit`.

SkillForge, EvolveCraft, multi-agent orchestration, and the full observability stack
are not started — see [ROADMAP.md](ROADMAP.md).
