import httpx
from pydantic import BaseModel

from app.config import settings


class InferenceResult(BaseModel):
    provider: str
    model: str
    text: str


def _pick_tier(prompt: str) -> str:
    return "large" if len(prompt) > settings.infercraft_large_prompt_chars else "small"


async def route_and_generate(prompt: str, max_tokens: int) -> InferenceResult:
    """Picks a provider based on what's configured and the prompt size, then calls it.

    Routing is intentionally simple for Phase 1: prefer whichever real provider has
    credentials/endpoint configured, escalate to a bigger model on longer prompts.
    Falls back to a stub so the endpoint works with zero configuration.
    """
    tier = _pick_tier(prompt)

    if settings.anthropic_api_key:
        model = "claude-opus-4-5" if tier == "large" else "claude-haiku-4-5"
        return await _call_anthropic(prompt, max_tokens, model)

    if settings.openai_api_key:
        model = "gpt-4o" if tier == "large" else "gpt-4o-mini"
        return await _call_openai(prompt, max_tokens, model)

    ollama_model = await _probe_ollama()
    if ollama_model:
        return await _call_ollama(prompt, max_tokens, ollama_model)

    return InferenceResult(
        provider="stub",
        model="none",
        text=f"[stub] no LLM provider configured (set OPENAI_API_KEY, ANTHROPIC_API_KEY, "
             f"or run Ollama) — echoing prompt tier={tier}, {len(prompt)} chars",
    )


async def _call_anthropic(prompt: str, max_tokens: int, model: str) -> InferenceResult:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]},
        )
        resp.raise_for_status()
        data = resp.json()
        text = "".join(block.get("text", "") for block in data.get("content", []))
        return InferenceResult(provider="anthropic", model=model, text=text)


async def _call_openai(prompt: str, max_tokens: int, model: str) -> InferenceResult:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]},
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        return InferenceResult(provider="openai", model=model, text=text)


# Embedding-only models (e.g. MemoryMesh's all-minilm) can't serve /api/generate
# and return a 400 if picked; their family is reported as "bert" by Ollama, unlike
# generation-capable models (llama, qwen, mistral, ...).
_EMBEDDING_ONLY_FAMILIES = {"bert"}


async def _probe_ollama() -> str | None:
    async with httpx.AsyncClient(timeout=2.0) as client:
        try:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            resp.raise_for_status()
            models = resp.json().get("models", [])
            for model in models:
                families = set(model.get("details", {}).get("families") or [])
                if not families & _EMBEDDING_ONLY_FAMILIES:
                    return model["name"]
            return None
        except httpx.HTTPError:
            return None


async def _call_ollama(prompt: str, max_tokens: int, model: str) -> InferenceResult:
    # Cold model loads on CPU-only/low-RAM hosts routinely take 60-90s+;
    # a tight timeout here surfaces as a client-side "Failed to fetch" with
    # no CORS header, since the connection drops before FastAPI can respond.
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False, "options": {"num_predict": max_tokens}},
        )
        resp.raise_for_status()
        return InferenceResult(provider="ollama", model=model, text=resp.json().get("response", ""))
