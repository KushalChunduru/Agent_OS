import httpx
from fastapi import Depends, FastAPI, Request

from app.audit import log_decision
from app.auth import require_auth
from app.config import settings
from app.policy import PromptRequest, enforce_policy
from app.rate_limit import check_rate_limit

app = FastAPI(title="Govrix Gateway", version="0.1.0")


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
        log_decision(user, req.agent_id, "submit_prompt", allowed=False, detail="policy_block")
        raise

    log_decision(user, req.agent_id, "submit_prompt", allowed=True)

    # Phase 1 stub: no MemoryMesh retrieval or InferCraft routing wired up yet.
    # This just echoes back so the dashboard has something to call end-to-end.
    return {
        "agent_id": req.agent_id,
        "user": user,
        "response": f"[stub] received prompt of {len(req.prompt)} chars, "
                     f"InferCraft routing not yet implemented",
    }


@app.get("/v1/memory/{agent_id}")
async def get_memory(agent_id: str) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{settings.memory_service_url}/v1/memories/{agent_id}")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            return {"error": str(exc), "agent_id": agent_id}
