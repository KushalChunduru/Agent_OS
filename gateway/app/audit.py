import logging
import time

import aiosqlite

logger = logging.getLogger("govrix.audit")
logging.basicConfig(level=logging.INFO)

AUDIT_DB_PATH = "audit.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    user TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    action TEXT NOT NULL,
    allowed INTEGER NOT NULL,
    detail TEXT NOT NULL DEFAULT ''
)
"""


async def init_audit_db() -> None:
    async with aiosqlite.connect(AUDIT_DB_PATH) as db:
        await db.execute(_CREATE_TABLE)
        await db.commit()


async def log_decision(user: str, agent_id: str, action: str, allowed: bool, detail: str = "") -> None:
    ts = time.time()
    logger.info(
        "audit ts=%s user=%s agent=%s action=%s allowed=%s detail=%s",
        ts, user, agent_id, action, allowed, detail,
    )
    async with aiosqlite.connect(AUDIT_DB_PATH) as db:
        await db.execute(
            "INSERT INTO audit_log (ts, user, agent_id, action, allowed, detail) VALUES (?, ?, ?, ?, ?, ?)",
            (ts, user, agent_id, action, int(allowed), detail),
        )
        await db.commit()


async def list_recent(limit: int = 100) -> list[dict]:
    async with aiosqlite.connect(AUDIT_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, ts, user, agent_id, action, allowed, detail FROM audit_log ORDER BY ts DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": row["id"],
                "ts": row["ts"],
                "user": row["user"],
                "agent_id": row["agent_id"],
                "action": row["action"],
                "allowed": bool(row["allowed"]),
                "detail": row["detail"],
            }
            for row in rows
        ]
