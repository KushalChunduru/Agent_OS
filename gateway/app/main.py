from contextlib import asynccontextmanager
from typing import Literal

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agents import create_agent, delete_agent, get_agent, init_agents_db, list_agents
from app.audit import init_audit_db, list_recent, log_decision
from app.auth import require_auth
from app.config import settings
from app.infercraft import route_and_generate
from app.memory_client import search_memories, store_memory
from app.policy import PromptRequest, enforce_policy
from app.rate_limit import check_rate_limit
from app.tools import TOOL_SCHEMAS


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_audit_db()
    await init_agents_db()
    yield


app = FastAPI(title="Govrix Gateway", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.dashboard_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "govrix-gateway"}


@app.post("/v1/prompt")
async def submit_prompt(req: PromptRequest, request: Request, claims: dict = Depends(require_auth)) -> dict:
    """Every prompt flows through here: auth -> rate limit -> policy -> (memory) -> LLM."""
    user = claims.get("sub", "unknown")
    check_rate_limit(request, client_id=user)

    try:
        enforce_policy(req)
    except Exception:
        await log_decision(user, req.agent_id, "submit_prompt", allowed=False, detail="policy_block")
        raise

    await log_decision(user, req.agent_id, "submit_prompt", allowed=True)

    # req.agent_id may reference a registered agent (with a persona/tier) or be
    # an ad-hoc string (existing behavior) — either way the request still works.
    agent = await get_agent(req.agent_id)

    memories = await search_memories(req.agent_id, req.prompt)
    context = "\n".join(f"- {m['content']}" for m in memories) if memories else ""

    messages = []
    if agent and agent["system_prompt"]:
        messages.append({"role": "system", "content": agent["system_prompt"]})
    if context:
        messages.append({"role": "system", "content": f"Relevant context from memory:\n{context}"})
    messages.append({"role": "user", "content": req.prompt})

    forced_tier = agent["model_tier"] if agent else None

    try:
        result = await route_and_generate(messages, req.max_tokens, tools=TOOL_SCHEMAS, forced_tier=forced_tier)
    except httpx.HTTPError as exc:
        await log_decision(user, req.agent_id, "submit_prompt", allowed=True, detail=f"inference_error: {exc}")
        raise HTTPException(status_code=502, detail=f"Inference provider error: {exc}") from exc

    await store_memory(req.agent_id, f"User asked: {req.prompt}", kind="episodic")
    await store_memory(req.agent_id, f"Agent replied: {result.text}", kind="episodic")

    return {
        "agent_id": req.agent_id,
        "user": user,
        "response": result.text,
        "provider": result.provider,
        "model": result.model,
        "memories_used": len(memories),
        "tool_calls": [tc.model_dump() for tc in result.tool_calls],
    }


@app.get("/v1/memory/{agent_id}")
async def get_memory(agent_id: str) -> list[dict] | dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{settings.memory_service_url}/v1/memories/{agent_id}")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            return {"error": str(exc), "agent_id": agent_id}


@app.get("/v1/audit")
async def get_audit_log(limit: int = 100) -> list[dict]:
    return await list_recent(limit=min(limit, 500))


class AgentIn(BaseModel):
    name: str
    system_prompt: str | None = None
    model_tier: Literal["small", "large", "reasoning"] = "small"


@app.post("/v1/agents")
async def create_agent_endpoint(payload: AgentIn) -> dict:
    return await create_agent(payload.name, payload.system_prompt, payload.model_tier)


@app.get("/v1/agents")
async def list_agents_endpoint() -> list[dict]:
    return await list_agents()


@app.get("/v1/agents/{agent_id}")
async def get_agent_endpoint(agent_id: str) -> dict:
    agent = await get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@app.delete("/v1/agents/{agent_id}")
async def delete_agent_endpoint(agent_id: str) -> dict:
    await delete_agent(agent_id)
    return {"deleted": agent_id}
