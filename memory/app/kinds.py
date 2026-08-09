import math
from datetime import datetime, timedelta, timezone
from typing import TypedDict


class MemoryRecord(TypedDict):
    id: str
    agent_id: str
    kind: str
    content: str
    created_at: datetime


WORKING_MEMORY_TTL_MINUTES = 60
EPISODIC_RECENCY_HALF_LIFE_HOURS = 24
EPISODIC_RECENCY_WEIGHT = 0.15


def is_expired(record: MemoryRecord, now: datetime | None = None) -> bool:
    """Working memory is session-scoped and expires; everything else is durable."""
    if record["kind"] != "working":
        return False
    now = now or datetime.now(timezone.utc)
    return now - record["created_at"] > timedelta(minutes=WORKING_MEMORY_TTL_MINUTES)


def recency_boost(record: MemoryRecord, now: datetime | None = None) -> float:
    """Episodic memories rank higher when recent, decaying over EPISODIC_RECENCY_HALF_LIFE_HOURS.

    Semantic and long_term memories are treated as equally relevant regardless of
    age, since they represent durable facts rather than events in a timeline.
    """
    if record["kind"] != "episodic":
        return 0.0
    now = now or datetime.now(timezone.utc)
    age_hours = (now - record["created_at"]).total_seconds() / 3600
    return EPISODIC_RECENCY_WEIGHT * math.exp(-age_hours / EPISODIC_RECENCY_HALF_LIFE_HOURS)
