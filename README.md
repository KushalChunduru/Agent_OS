# AgentOS

A self-hosted operating system for autonomous AI agents — governance, memory, inference routing, and observability as isolated, swappable services instead of one monolithic chatbot.

This repo currently implements the **Phase 1 MVP** slice of the full design (see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the target architecture):

- **Govrix** (`gateway/`) — FastAPI gateway: every request is authenticated, rate-limited, and policy-checked before it reaches an LLM.
- **MemoryMesh** (`memory/`) — FastAPI service backed by Postgres + pgvector for storing and retrieving embeddings.
- **Dashboard** (`dashboard/`) — Next.js + Tailwind console for agent management and live status.
- **Storage** — Postgres (with pgvector extension) + Redis, via Docker Compose.

Later phases (InferCraft model routing, SkillForge skill mining, EvolveCraft self-improvement loop, full observability stack) are scoped in [docs/ROADMAP.md](docs/ROADMAP.md) and will be added incrementally.

## Quick start

```bash
cp .env.example .env
docker compose -f docker/docker-compose.yml up --build
```

- Gateway: http://localhost:8000/health
- MemoryMesh: http://localhost:8001/health
- Dashboard: http://localhost:3000

## Repo layout

```
agent-os/
├── gateway/     # Govrix — governance & security gateway (FastAPI)
├── memory/      # MemoryMesh — persistent memory service (FastAPI + pgvector)
├── dashboard/   # L0 console (Next.js + Tailwind)
├── docker/      # docker-compose.yml + service Dockerfiles
├── docs/        # architecture & roadmap
└── .github/     # CI workflows
```

## Status

Early scaffold — Phase 1 of the roadmap. See [docs/ROADMAP.md](docs/ROADMAP.md) for what's next.
