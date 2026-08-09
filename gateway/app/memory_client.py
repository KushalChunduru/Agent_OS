import logging

import httpx

from app.config import settings

logger = logging.getLogger("govrix.memory_client")

# MemoryMesh's own embed() call can cold-load an Ollama embedding model
# (memory/app/embeddings.py uses a 30s timeout for that); give this client
# enough headroom to outlast it instead of silently returning empty results.
_TIMEOUT = 40.0


async def search_memories(agent_id: str, query: str, top_k: int = 5) -> list[dict]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            resp = await client.post(
                f"{settings.memory_service_url}/v1/memories/search",
                json={"agent_id": agent_id, "query": query, "top_k": top_k},
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.warning("MemoryMesh search failed, continuing with no context: %s", exc)
            return []


async def store_memory(agent_id: str, content: str, kind: str = "episodic") -> None:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            await client.post(
                f"{settings.memory_service_url}/v1/memories",
                json={"agent_id": agent_id, "content": content, "kind": kind},
            )
        except httpx.HTTPError as exc:
            logger.warning("MemoryMesh store failed, exchange will not be remembered: %s", exc)
