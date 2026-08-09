from datetime import datetime, timezone

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from app.config import settings

COLLECTION = "memories"

# Embedded/local mode: Qdrant runs in-process against a local directory, no
# server or Docker required. Client calls are synchronous but fast enough at
# this scale to call directly from async route handlers without a thread pool.
_client = QdrantClient(path=settings.qdrant_path)
_collection_ready = False


def _ensure_collection() -> None:
    global _collection_ready
    if _collection_ready:
        return
    if not _client.collection_exists(COLLECTION):
        _client.create_collection(
            collection_name=COLLECTION,
            vectors_config=qm.VectorParams(size=settings.embedding_dim, distance=qm.Distance.COSINE),
        )
    _collection_ready = True


def _record_to_dict(point, score: float | None = None) -> dict:
    payload = point.payload or {}
    record = {
        "id": str(point.id),
        "agent_id": payload["agent_id"],
        "kind": payload["kind"],
        "content": payload["content"],
        "created_at": datetime.fromisoformat(payload["created_at"]),
    }
    if score is not None:
        record["score"] = score
    return record


def upsert_memory(memory_id: str, agent_id: str, kind: str, content: str, embedding: list[float]) -> dict:
    _ensure_collection()
    created_at = datetime.now(timezone.utc)
    _client.upsert(
        collection_name=COLLECTION,
        points=[
            qm.PointStruct(
                id=memory_id,
                vector=embedding,
                payload={
                    "agent_id": agent_id,
                    "kind": kind,
                    "content": content,
                    "created_at": created_at.isoformat(),
                },
            )
        ],
    )
    return {"id": memory_id, "agent_id": agent_id, "kind": kind, "content": content, "created_at": created_at}


def delete_memories(memory_ids: list[str]) -> None:
    if not memory_ids:
        return
    _client.delete(collection_name=COLLECTION, points_selector=qm.PointIdsList(points=memory_ids))


def list_memories(agent_id: str) -> list[dict]:
    _ensure_collection()
    points, _ = _client.scroll(
        collection_name=COLLECTION,
        scroll_filter=qm.Filter(must=[qm.FieldCondition(key="agent_id", match=qm.MatchValue(value=agent_id))]),
        limit=1000,
        with_payload=True,
    )
    records = [_record_to_dict(p) for p in points]
    records.sort(key=lambda r: r["created_at"], reverse=True)
    return records


def search_memories(agent_id: str, query_vector: list[float], limit: int) -> list[dict]:
    _ensure_collection()
    result = _client.query_points(
        collection_name=COLLECTION,
        query=query_vector,
        query_filter=qm.Filter(must=[qm.FieldCondition(key="agent_id", match=qm.MatchValue(value=agent_id))]),
        # Over-fetch so recency-boost re-ranking (kinds.recency_boost) has
        # more than just the top-`limit` raw-similarity hits to work with.
        limit=max(limit * 4, 20),
        with_payload=True,
    )
    return [_record_to_dict(p, score=p.score) for p in result.points]
