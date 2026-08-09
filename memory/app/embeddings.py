import hashlib
import logging
import math
import re

import httpx

from app.config import settings

logger = logging.getLogger("memorymesh.embeddings")

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _hash_embed(text: str) -> list[float]:
    """Deterministic hashing-trick embedding: no model, no network call.

    Used only as a fallback when Ollama's embedding endpoint is unreachable,
    so the service stays usable (with weaker relevance ranking) instead of
    failing outright.
    """
    vec = [0.0] * settings.embedding_dim
    tokens = _TOKEN_RE.findall(text.lower())
    for token in tokens:
        digest = hashlib.sha256(token.encode()).digest()
        bucket = int.from_bytes(digest[:4], "big") % settings.embedding_dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[bucket] += sign

    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


async def embed(text: str) -> list[float]:
    """Real embedding via Ollama's /api/embeddings, falling back to a hash
    approximation if Ollama isn't reachable (e.g. not installed/running).
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/embeddings",
                json={"model": settings.embedding_model, "prompt": text},
            )
            resp.raise_for_status()
            vector = resp.json().get("embedding")
            if vector:
                return vector
    except httpx.HTTPError as exc:
        logger.warning("Ollama embedding call failed, falling back to hash embedding: %s", exc)

    return _hash_embed(text)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (norm_a * norm_b)
