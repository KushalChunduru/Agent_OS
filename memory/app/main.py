from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Base, engine, get_session
from app.embeddings import cosine_similarity, embed
from app.models import Memory


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="MemoryMesh", version="0.1.0", lifespan=lifespan)


class MemoryIn(BaseModel):
    agent_id: str
    content: str
    kind: str = "semantic"


class MemoryOut(BaseModel):
    id: str
    agent_id: str
    kind: str
    content: str

    class Config:
        from_attributes = True


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "memorymesh"}


@app.post("/v1/memories", response_model=MemoryOut)
async def store_memory(payload: MemoryIn, session: AsyncSession = Depends(get_session)) -> Memory:
    memory = Memory(
        agent_id=payload.agent_id,
        kind=payload.kind,
        content=payload.content,
        embedding=embed(payload.content),
    )
    session.add(memory)
    await session.commit()
    await session.refresh(memory)
    return memory


@app.get("/v1/memories/{agent_id}", response_model=list[MemoryOut])
async def list_memories(agent_id: str, session: AsyncSession = Depends(get_session)) -> list[Memory]:
    result = await session.execute(select(Memory).where(Memory.agent_id == agent_id).order_by(Memory.created_at.desc()))
    return list(result.scalars())


class SearchRequest(BaseModel):
    agent_id: str
    query: str
    top_k: int = 5


@app.post("/v1/memories/search", response_model=list[MemoryOut])
async def search_memories(payload: SearchRequest, session: AsyncSession = Depends(get_session)) -> list[Memory]:
    query_vec = embed(payload.query)
    result = await session.execute(select(Memory).where(Memory.agent_id == payload.agent_id))
    candidates = list(result.scalars())
    candidates.sort(key=lambda m: cosine_similarity(m.embedding, query_vec), reverse=True)
    return candidates[: payload.top_k]
