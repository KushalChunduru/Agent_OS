from fastapi import HTTPException, status
from pydantic import BaseModel

# Deny-list of substrings that block a prompt outright. This is a placeholder
# for real policy enforcement (PII detection, jailbreak classifiers, tool
# allow-lists per agent) — not production moderation.
BLOCKED_PATTERNS = ["ignore previous instructions", "system prompt override"]

MAX_PROMPT_CHARS = 8000


class PromptRequest(BaseModel):
    agent_id: str
    prompt: str
    max_tokens: int = 512


def enforce_policy(req: PromptRequest) -> None:
    if len(req.prompt) > MAX_PROMPT_CHARS:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Prompt exceeds {MAX_PROMPT_CHARS} character limit",
        )

    lowered = req.prompt.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in lowered:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Prompt blocked by policy",
            )
