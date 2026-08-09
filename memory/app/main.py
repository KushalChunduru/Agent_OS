import uuid
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from app.embeddings import embed
from app.kinds import is_expired, recency_boost
from app.vectorstore import delete_memories, list_memories, search_memories, upsert_memory

MemoryKind = Literal["working", "episodic", "semantic", "long_term"]

app = FastAPI(title="MemoryMesh", version="0.1.0")


class MemoryIn(BaseModel):
    agent_id: str
    content: str
    kind: MemoryKind = "semantic"


class MemoryOut(BaseModel):
    id: str
    agent_id: str
    kind: str
    content: str


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "memorymesh"}


@app.post("/v1/memories", response_model=MemoryOut)
async def store_memory(payload: MemoryIn) -> dict:
    embedding = await embed(payload.content)
    memory_id = str(uuid.uuid4())
    return upsert_memory(memory_id, payload.agent_id, payload.kind, payload.content, embedding)


def _prune_expired_working(records: list[dict]) -> list[dict]:
    """Working memory is session-scoped; drop expired entries and delete them lazily on read."""
    live, expired_ids = [], []
    for r in records:
        if is_expired(r):
            expired_ids.append(r["id"])
        else:
            live.append(r)
    delete_memories(expired_ids)
    return live


@app.get("/v1/memories/{agent_id}", response_model=list[MemoryOut])
async def list_memories_endpoint(agent_id: str) -> list[dict]:
    return _prune_expired_working(list_memories(agent_id))


class SearchRequest(BaseModel):
    agent_id: str
    query: str
    top_k: int = 5


@app.post("/v1/memories/search", response_model=list[MemoryOut])
async def search_memories_endpoint(payload: SearchRequest) -> list[dict]:
    query_vec = await embed(payload.query)
    candidates = _prune_expired_working(search_memories(payload.agent_id, query_vec, payload.top_k))
    candidates.sort(key=lambda r: r["score"] + recency_boost(r), reverse=True)
    return candidates[: payload.top_k]
