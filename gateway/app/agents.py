import time
import uuid

import aiosqlite

AGENTS_DB_PATH = "agents.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    system_prompt TEXT,
    model_tier TEXT NOT NULL DEFAULT 'small',
    created_at REAL NOT NULL
)
"""


async def init_agents_db() -> None:
    async with aiosqlite.connect(AGENTS_DB_PATH) as db:
        await db.execute(_CREATE_TABLE)
        await db.commit()


def _row_to_dict(row: aiosqlite.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "system_prompt": row["system_prompt"],
        "model_tier": row["model_tier"],
        "created_at": row["created_at"],
    }


async def create_agent(name: str, system_prompt: str | None, model_tier: str) -> dict:
    agent_id = str(uuid.uuid4())
    created_at = time.time()
    async with aiosqlite.connect(AGENTS_DB_PATH) as db:
        await db.execute(
            "INSERT INTO agents (id, name, system_prompt, model_tier, created_at) VALUES (?, ?, ?, ?, ?)",
            (agent_id, name, system_prompt, model_tier, created_at),
        )
        await db.commit()
    return {
        "id": agent_id,
        "name": name,
        "system_prompt": system_prompt,
        "model_tier": model_tier,
        "created_at": created_at,
    }


async def list_agents() -> list[dict]:
    async with aiosqlite.connect(AGENTS_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM agents ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [_row_to_dict(row) for row in rows]


async def get_agent(agent_id: str) -> dict | None:
    async with aiosqlite.connect(AGENTS_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        row = await cursor.fetchone()
        return _row_to_dict(row) if row else None


async def delete_agent(agent_id: str) -> None:
    async with aiosqlite.connect(AGENTS_DB_PATH) as db:
        await db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        await db.commit()
