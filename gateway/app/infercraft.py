import json
from typing import Literal

import httpx
from pydantic import BaseModel

from app.config import settings
from app.tools import execute_tool

ModelTier = Literal["small", "large", "reasoning"]

MAX_TOOL_ROUNDS = 3


class ToolCallRecord(BaseModel):
    name: str
    arguments: dict
    result: str


class InferenceResult(BaseModel):
    provider: str
    model: str
    text: str
    tool_calls: list[ToolCallRecord] = []


def _pick_tier(messages: list[dict], tools_enabled: bool, forced_tier: ModelTier | None) -> ModelTier:
    if forced_tier:
        return forced_tier
    if tools_enabled:
        # Tool-use benefits from the more capable end of a provider's lineup.
        return "reasoning"
    total_chars = sum(len(m.get("content") or "") for m in messages)
    return "large" if total_chars > settings.infercraft_large_prompt_chars else "small"


async def route_and_generate(
    messages: list[dict],
    max_tokens: int,
    tools: list[dict] | None = None,
    forced_tier: ModelTier | None = None,
) -> InferenceResult:
    """Picks a provider based on what's configured and the request shape, then calls it.

    Routing prefers whichever real provider has credentials configured, escalates
    model tier on longer prompts (or to "reasoning" whenever tools are enabled, since
    tool-use benefits from more capable models), and falls back to a stub so the
    endpoint works with zero configuration.
    """
    tier = _pick_tier(messages, tools_enabled=bool(tools), forced_tier=forced_tier)

    if settings.anthropic_api_key:
        model = {"small": "claude-haiku-4-5", "large": "claude-opus-4-5", "reasoning": "claude-opus-4-5"}[tier]
        return await _call_anthropic(messages, max_tokens, model, tools)

    if settings.openai_api_key:
        model = {"small": "gpt-4o-mini", "large": "gpt-4o", "reasoning": "gpt-4o"}[tier]
        return await _call_openai(messages, max_tokens, model, tools)

    ollama_model = await _probe_ollama()
    if ollama_model:
        return await _call_ollama(messages, max_tokens, ollama_model, tools)

    prompt_chars = sum(len(m.get("content") or "") for m in messages)
    return InferenceResult(
        provider="stub",
        model="none",
        text=f"[stub] no LLM provider configured (set OPENAI_API_KEY, ANTHROPIC_API_KEY, "
             f"or run Ollama) — echoing prompt tier={tier}, {prompt_chars} chars",
    )


def _anthropic_tools(tools: list[dict]) -> list[dict]:
    # Anthropic's tool shape is flatter than OpenAI/Ollama's {"type": "function", "function": {...}}.
    return [
        {"name": t["function"]["name"], "description": t["function"]["description"], "input_schema": t["function"]["parameters"]}
        for t in tools
    ]


async def _call_anthropic(messages: list[dict], max_tokens: int, model: str, tools: list[dict] | None) -> InferenceResult:
    tool_calls: list[ToolCallRecord] = []
    conversation = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
    system_text = next((m["content"] for m in messages if m["role"] == "system"), None)

    async with httpx.AsyncClient(timeout=30.0) as client:
        for _ in range(MAX_TOOL_ROUNDS):
            body: dict = {"model": model, "max_tokens": max_tokens, "messages": conversation}
            if system_text:
                body["system"] = system_text
            if tools:
                body["tools"] = _anthropic_tools(tools)

            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
            content_blocks = data.get("content", [])
            tool_use_blocks = [b for b in content_blocks if b.get("type") == "tool_use"]

            if not tool_use_blocks:
                text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
                return InferenceResult(provider="anthropic", model=model, text=text, tool_calls=tool_calls)

            conversation.append({"role": "assistant", "content": content_blocks})
            tool_results = []
            for block in tool_use_blocks:
                result = execute_tool(block["name"], block.get("input", {}))
                tool_calls.append(ToolCallRecord(name=block["name"], arguments=block.get("input", {}), result=result))
                tool_results.append({"type": "tool_result", "tool_use_id": block["id"], "content": result})
            conversation.append({"role": "user", "content": tool_results})

    return InferenceResult(provider="anthropic", model=model, text="[no final answer after max tool rounds]", tool_calls=tool_calls)


async def _call_openai(messages: list[dict], max_tokens: int, model: str, tools: list[dict] | None) -> InferenceResult:
    tool_calls: list[ToolCallRecord] = []
    conversation = list(messages)

    async with httpx.AsyncClient(timeout=30.0) as client:
        for _ in range(MAX_TOOL_ROUNDS):
            body: dict = {"model": model, "max_tokens": max_tokens, "messages": conversation}
            if tools:
                body["tools"] = tools

            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
            message = data["choices"][0]["message"]
            requested_calls = message.get("tool_calls") or []

            if not requested_calls:
                return InferenceResult(provider="openai", model=model, text=message.get("content") or "", tool_calls=tool_calls)

            conversation.append(message)
            for call in requested_calls:
                name = call["function"]["name"]
                arguments = json.loads(call["function"]["arguments"] or "{}")
                result = execute_tool(name, arguments)
                tool_calls.append(ToolCallRecord(name=name, arguments=arguments, result=result))
                conversation.append({"role": "tool", "tool_call_id": call["id"], "content": result})

    return InferenceResult(provider="openai", model=model, text="[no final answer after max tool rounds]", tool_calls=tool_calls)


# Embedding-only models (e.g. MemoryMesh's all-minilm) can't serve /api/chat generation
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


async def _call_ollama(messages: list[dict], max_tokens: int, model: str, tools: list[dict] | None) -> InferenceResult:
    tool_calls: list[ToolCallRecord] = []
    conversation = list(messages)

    # Cold model loads on CPU-only/low-RAM hosts routinely take 60-90s+;
    # a tight timeout here surfaces as a client-side "Failed to fetch" with
    # no CORS header, since the connection drops before FastAPI can respond.
    async with httpx.AsyncClient(timeout=180.0) as client:
        for _ in range(MAX_TOOL_ROUNDS):
            body: dict = {
                "model": model,
                "messages": conversation,
                "stream": False,
                "options": {"num_predict": max_tokens},
            }
            if tools:
                body["tools"] = tools

            resp = await client.post(f"{settings.ollama_base_url}/api/chat", json=body)
            resp.raise_for_status()
            message = resp.json().get("message", {})
            requested_calls = message.get("tool_calls") or []

            if not requested_calls:
                return InferenceResult(provider="ollama", model=model, text=message.get("content", ""), tool_calls=tool_calls)

            conversation.append(message)
            for call in requested_calls:
                fn = call["function"]
                name, arguments = fn["name"], fn.get("arguments") or {}
                result = execute_tool(name, arguments)
                tool_calls.append(ToolCallRecord(name=name, arguments=arguments, result=result))
                conversation.append({"role": "tool", "content": result})

    return InferenceResult(provider="ollama", model=model, text="[no final answer after max tool rounds]", tool_calls=tool_calls)
