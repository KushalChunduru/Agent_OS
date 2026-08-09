# Roadmap

## Progress at a glance

| # | Phase | Status |
|---|---|:---:|
| 1 | Core Platform | ✅ Done |
| 2 | Memory & Retrieval | ✅ Done |
| 3 | Multi-Agent System | ✅ Done |
| 4 | Skill Management | ⏳ Not started |
| 5 | Observability | ⏳ Not started |
| 6 | Improvement Engine | ⏳ Not started |

---

## Phase 1 — Core Platform ✅

- [x] FastAPI gateway (Govrix) with health check, auth, rate limiting, policy enforcement, audit logging, CORS
- [x] FastAPI MemoryMesh — store/list/search endpoints
- [x] Next.js + Tailwind dashboard shell
- [x] Native run path (no Docker/WSL required) — verified end-to-end locally
- [x] Docker Compose as an alternative path (Redis, gateway, memory, dashboard)
- [x] Wire dashboard → gateway end to end (health check over CORS)
- [x] Wire gateway `/v1/prompt` → MemoryMesh retrieval → InferCraft → response, storing the exchange back
- [x] InferCraft routing to OpenAI / Anthropic / Ollama when configured, falls back to a labeled stub with zero config
- [x] Dashboard UI for sending prompts and viewing responses (agent console + live memory panel)
- [x] Verified live with a real local model (Ollama `llama3.2:1b`) — full loop confirmed: prompt → memory retrieval → inference → response → memory storage

## Phase 2 — Memory & Retrieval ✅

- [x] Real embedding model — Ollama `all-minilm` (384-dim), replacing the Phase 1 hashing approximation. Falls back to the hash embedding if Ollama is unreachable so the service degrades instead of failing outright.
- [x] Qdrant integration — swapped SQLite's brute-force cosine scan for `qdrant-client`'s embedded/local mode (no server, no Docker; data lives in `memory/qdrant_data/`). MemoryMesh no longer has a SQL database at all.
- [x] Working / episodic / semantic / long_term memory types now have real behavior: `working` expires after 60 minutes and is pruned lazily on read; `episodic` gets an exponentially-decaying recency boost in search ranking; `semantic`/`long_term` are stable regardless of age. See `memory/app/kinds.py`.
- [x] Audit logging persisted to SQLite (`gateway/audit.db`) via `gateway/app/audit.py`, queryable at `GET /v1/audit`. Console logging kept alongside.

> **Storage note:** MemoryMesh's Qdrant runs in **embedded/local mode** — it's a
> Python-in-process index backed by a local directory, not a server. This keeps
> the native (no-Docker) run path intact. Local mode file-locks its data
> directory, so only one MemoryMesh process can run against it at a time.

## Phase 3 — Multi-Agent System ✅

- [x] Agent registry — named agents with a persona (`system_prompt`) and preferred model
      tier, persisted in SQLite (`gateway/agents.db`) via `gateway/app/agents.py`.
      `POST/GET/DELETE /v1/agents`. `/v1/prompt` looks up `agent_id` in the registry;
      unregistered IDs (e.g. `"demo"`) still work exactly as before — fully backward
      compatible.
- [x] Task orchestration, scoped to a **bounded synchronous tool-calling loop** rather
      than a persistent async task queue (deliberate scope decision — see below): the
      agent can call tools mid-response, the gateway executes them and feeds results
      back, up to 3 rounds, all within one request/response. No background workers,
      no task table.
- [x] Tool execution framework — `gateway/app/tools.py`: `calculate` (safe arithmetic
      via Python's `ast` module, **no `eval()`** — confirmed it rejects an injection
      payload like `__import__("os").system(...)` rather than executing it) and
      `get_current_time`. Unknown tool names or bad arguments return an error string
      instead of raising, so a bad tool call can't crash a request.
- [x] InferCraft routing refinement — added a third `reasoning` tier alongside the
      existing `small`/`large` length-based split, auto-selected whenever tools are
      enabled (tool-use benefits from more capable models). A registered agent's
      `model_tier` overrides the heuristic.

> **What's verified live vs. implemented-but-untested:** The Ollama tool-calling path
> (`/api/chat`, switched from `/api/generate` which doesn't support tools) is verified
> live end-to-end — calculator and time tools both execute correctly and the model
> incorporates results into a correct final answer (confirmed: 128×37=4736, 65×12=780).
> Anthropic and OpenAI tool-calling code paths exist and follow each provider's
> documented wire format, but are **not live-tested** in this environment (no API key
> configured here).
>
> **Known limitation:** `llama3.2:1b` is unreliable at *choosing* the right tool once
> the request includes a system prompt and injected memory context — it sometimes
> calls `calculate` with a non-numeric expression instead of `get_current_time`, or
> emits pseudo-JSON instead of a real tool call. This reproduces even in isolation
> once enough context is added; it does **not** happen with a bare question and no
> system prompt. The framework itself handles this safely (errors are returned to the
> model, not raised), so it degrades to a slightly rambling but still-correct text
> answer rather than crashing. Expected to be more reliable with a larger local model
> or with Anthropic/OpenAI.
>
> **Why a bounded loop instead of a task queue:** a persistent async task queue needs
> a task table, a background runner, and a polling/streaming UI — a materially bigger
> lift than what "task orchestration" needed to prove out for this phase. The bounded
> loop delivers the actual user-facing capability (agents that can act, not just
> talk) without that infrastructure; a task queue remains a natural Phase 4+ addition
> if agents need to run long, unattended, multi-step jobs.

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
