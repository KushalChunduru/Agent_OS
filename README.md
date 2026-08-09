# AgentOS

A self-hosted operating system for autonomous AI agents — governance, memory, inference routing, and observability as isolated, swappable services instead of one monolithic chatbot.

This repo currently implements the **Phase 1 MVP** slice of the full design (see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the target architecture):

- **Govrix** (`gateway/`) — FastAPI gateway: every request is authenticated, rate-limited, and policy-checked before it reaches an LLM. CORS-enabled for the dashboard.
- **MemoryMesh** (`memory/`) — FastAPI service backed by SQLite, storing embeddings and doing similarity search in-process. No external vector DB or model download required — swap in pgvector/Qdrant + a real embedding model later (see [docs/ROADMAP.md](docs/ROADMAP.md)).
- **Dashboard** (`dashboard/`) — Next.js + Tailwind console, currently shows live gateway health.
- **Storage** — SQLite file (`memory/memory.db`), created automatically on first run. Redis is optional (rate limiting falls back to in-memory if it's not running).

Later phases (InferCraft model routing, SkillForge skill mining, EvolveCraft self-improvement loop, full observability stack, Postgres/Qdrant/Neo4j storage) are scoped in [docs/ROADMAP.md](docs/ROADMAP.md) and will be added incrementally.

## Quick start (native, no Docker)

Requires Python 3.12+ and Node 20+.

```bash
cp .env.example .env
python -m venv .venv
```

Windows:
```bash
.venv/Scripts/pip install -r gateway/requirements.txt -r memory/requirements.txt
```

macOS/Linux:
```bash
.venv/bin/pip install -r gateway/requirements.txt -r memory/requirements.txt
```

Run each in its own terminal:

```bash
cd gateway && ../.venv/Scripts/python -m uvicorn app.main:app --port 8000
```
```bash
cd memory && ../.venv/Scripts/python -m uvicorn app.main:app --port 8001
```
```bash
cd dashboard && npm install && npm run dev
```

- Gateway: http://localhost:8000/health
- MemoryMesh: http://localhost:8001/health
- Dashboard: http://localhost:3000

## Getting real LLM responses (InferCraft)

By default `/v1/prompt` falls back to a stub echo — no LLM is configured. InferCraft picks a provider in this order: Anthropic (`ANTHROPIC_API_KEY`) → OpenAI (`OPENAI_API_KEY`) → local Ollama.

**Free, local option — Ollama:**

1. Install from [ollama.com](https://ollama.com) (already common on most dev machines).
2. Pull a model. On machines with 8GB RAM or less, use the small 1B model — the default 3B `llama3.2` needs ~2GB free RAM to load and will OOM on constrained systems:
   ```bash
   ollama pull llama3.2:1b
   ```
   With more RAM available, `ollama pull llama3.2` (3B) gives better answers.
3. Nothing else to configure — the gateway auto-detects a running Ollama at `http://localhost:11434` (override via `OLLAMA_BASE_URL` in `.env`) and picks whichever model you've pulled.
4. First response after a pull/restart is slow (model load into RAM, 30–70s on CPU); subsequent responses are much faster while Ollama keeps it warm.

**Paid option:** set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `.env` for faster, higher-quality responses (see `.env.example`).

## Quick start (Docker, optional)

```bash
cp .env.example .env
docker compose -f docker/docker-compose.yml up --build
```

## Repo layout

```
agent-os/
├── gateway/     # Govrix — governance & security gateway (FastAPI)
├── memory/      # MemoryMesh — persistent memory service (FastAPI + SQLite)
├── dashboard/   # L0 console (Next.js + Tailwind)
├── docker/      # docker-compose.yml + service Dockerfiles (optional path)
├── docs/        # architecture & roadmap
└── .github/     # CI workflows
```

## Status

Phase 1 MVP running end-to-end natively, including real LLM inference: dashboard
sends a prompt → gateway enforces auth/rate-limit/policy → MemoryMesh retrieves
relevant memories → InferCraft routes to a local Ollama model (or Anthropic/OpenAI
if configured) → response and exchange are stored back into memory. See
[docs/ROADMAP.md](docs/ROADMAP.md) for what's next.
