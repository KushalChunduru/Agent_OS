import time

from fastapi import HTTPException, Request, status

from app.config import settings

# In-memory fallback bucket keyed by client id. Swap for Redis-backed counters
# (see settings.redis_url) once the gateway runs as more than one replica.
_buckets: dict[str, list[float]] = {}


def check_rate_limit(request: Request, client_id: str) -> None:
    now = time.time()
    window_start = now - 60
    hits = _buckets.setdefault(client_id, [])
    hits[:] = [t for t in hits if t > window_start]

    if len(hits) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} requests/minute",
        )

    hits.append(now)
