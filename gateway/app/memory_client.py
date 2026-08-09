import httpx

from app.config import settings


async def search_memories(agent_id: str, query: str, top_k: int = 5) -> list[dict]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.post(
                f"{settings.memory_service_url}/v1/memories/search",
                json={"agent_id": agent_id, "query": query, "top_k": top_k},
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError:
            return []


async def store_memory(agent_id: str, content: str, kind: str = "episodic") -> None:
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            await client.post(
                f"{settings.memory_service_url}/v1/memories",
                json={"agent_id": agent_id, "content": content, "kind": kind},
            )
        except httpx.HTTPError:
            pass
