# Architecture

Full target design — most layers beyond Phase 1 + 2 are not yet implemented; see
[what's actually running today](#whats-actually-implemented-today) below and
[ROADMAP.md](ROADMAP.md) for the build order.

```mermaid
flowchart TD
    USER([User]) --> L0["L0 - Dashboard Console<br/>agent mgmt, live monitoring, skill marketplace, audit viewer"]

    L0 --> L1["L1 - Govrix Scout<br/>governance and security: prompt validation, tool permissions,<br/>cost limits, auth, rate limiting, policy enforcement, audit log"]

    L1 --> L2A & L2B & L2C

    L2A["L2A - MemoryMesh<br/>persistent memory: Qdrant, embeddings"]
    L2B["L2B - InferCraft<br/>model/prompt routing, GPU scheduling"]
    L2C["L2C - SkillForge<br/>mines repeated workflows into reusable skills<br/>design concept, not shipped"]

    L2A & L2B & L2C --> L2E["L2E - EvolveCraft<br/>self-improvement loop, MAPE-K: Monitor, Analyze, Plan, Execute, Knowledge.<br/>Never auto-applies changes - generates a diff, waits for human approval."]

    L2E --> L3["L3 - Storage Layer<br/>TimescaleDB, pgvector, Qdrant, Redis, Neo4j, ScyllaDB<br/>specialized store per workload, independently tunable"]

    L3 --> L4["L4 - Observability<br/>Prometheus, Grafana, RAGAS, Locust"]

    classDef live fill:#1a4d47,stroke:#2dd4bf,color:#ecebe7,stroke-width:2px
    classDef planned fill:#2a2a2a,stroke:#666,color:#999,stroke-dasharray: 4 3
    class L0,L1,L2A,L2B live
    class L2C,L2E,L3,L4 planned
```

*Teal = running code today. Dashed/grey = designed but not yet built.*

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

## Request flow

See the sequence diagram in the [README](../README.md#-see-it-work) for a
step-by-step trace of what happens between typing a prompt and seeing a response,
including exactly where governance, memory retrieval, and provider routing happen.
