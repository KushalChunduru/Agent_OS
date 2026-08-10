# AgentOS Demo Walkthrough

**Recorded demo:** [docs/demo/agentos-demo.mp4](demo/agentos-demo.mp4) —
a ~63s captioned walkthrough recorded live against a running instance
(landing page → governance/memory → tool-calling → live agent creation).
A version with a real toggleable subtitle track instead of burned-in
captions is at [docs/demo/agentos-demo-softsub.mp4](demo/agentos-demo-softsub.mp4).

A ~4-minute screen-recording script covering every implemented capability:
governance, memory, tool-calling, agent registry, and the landing page. Every
line below has been run against this exact codebase tonight — the numbers
and outputs are real, not illustrative.

**Before recording:** start all three services (see [README](../README.md#-quick-start))
and confirm `http://localhost:8000/health`, `http://localhost:8001/health`,
and `http://localhost:3000` all respond. Have `llama3.2:1b` and `all-minilm`
already pulled so responses aren't stuck on a cold-start model load — or budget
30–70s of screen time for that if you want to show it happening live (it's a
legitimate part of the "self-hosted, no API key" story).

---

## Scene 1 — Landing page (0:00–0:40)

1. Open `http://localhost:3000`.
2. Point out the **"GOVRIX GATEWAY — ONLINE"** pill at the top — say out loud
   that this is a live fetch to the running gateway, not a static badge.
3. Scroll to the **layered architecture diagram**. Narrate: *"L0 through L2B
   are marked LIVE — that's real, running code. L2C SkillForge and L2E
   EvolveCraft are marked PLANNED — I'm not claiming those exist."*
4. Scroll to **Capabilities** — read one card aloud (Governance first is a
   good one, it sets up Scene 2).
5. Click **Open Console**.

## Scene 2 — Governance in action (0:40–1:10)

1. On `/console`, point out the agent picker already has two agents from
   earlier testing: **"Math Tutor · reasoning"** — created via the registry,
   not hardcoded.
2. Say: *"Every request here goes through Govrix first — auth, a rate limit,
   a policy check — before anything touches an LLM."* (Optional: open a
   terminal and hit `GET http://localhost:8000/v1/audit` to show the
   persisted decision log — every one of these console messages left an
   audit trail.)

```bash
curl -s http://localhost:8000/v1/audit?limit=5
```

## Scene 3 — Memory that's actually semantic (1:10–2:00)

1. Select the **demo (ad-hoc)** agent (proves unregistered agent IDs still
   work — no registry lock-in).
2. Type: `My name is Kushal and I'm building AgentOS. Remember that.` → Send.
3. While it's thinking (cold Ollama load can take 30–70s), narrate: *"This
   is calling a fully local model — no API key, no cloud call. MemoryMesh is
   about to store this in a real Qdrant vector index, not a database row
   with a string match."*
4. Once it replies, ask a **semantically related but zero-word-overlap**
   follow-up: `What do you know about the person you're talking to?`
5. Point at `memories_used: N` in the meta line under the reply — say:
   *"That's not a hardcoded number. MemoryMesh actually searched a vector
   index and found this relevant."*
6. Click **Load memories** — show the MemoryMesh panel populate with the
   stored exchange, tagged `episodic`.

## Scene 4 — Tools actually executing (2:00–3:00)

1. Switch the agent picker to **Math Tutor**.
2. Type: `What is 83 times 46?` → Send.
3. While waiting, narrate: *"This agent has a system prompt telling it to use
   a calculator tool. Watch — the model is going to emit a real function
   call, my gateway executes it with a safe AST parser (no `eval`), and
   feeds the result back for a final answer."*
4. When the reply lands, point at the tool-call line rendered under the
   response: `🔧 calculate(83 * 46) → 3818` — say: *"That's not the model
   guessing arithmetic. It called a real Python function and got a real
   number back."* (83 × 46 = 3818 — verify on screen if you want extra
   credibility.)
5. **Honesty beat (worth keeping in — it's a strength, not a weakness):**
   say *"This is a 1B-parameter local model, so it isn't perfectly reliable
   at tool selection — sometimes it calls the wrong tool. I found and
   documented that limitation in the roadmap rather than hiding it. It's
   still safe either way: a bad tool call returns an error string, it never
   crashes the request."*

## Scene 5 — Creating an agent live (3:00–3:40)

1. Click **+ New agent**.
2. Fill in: name `Release Notes Bot`, system prompt
   `You write terse, factual release notes. No fluff.`, tier `large`.
3. Click **Create** — point out it's immediately selected and usable, backed
   by a real SQLite row in `gateway/agents.db` (optionally show
   `curl http://localhost:8000/v1/agents` in a terminal split).
4. Send it one prompt to prove it's alive with its new persona.

## Scene 6 — Wrap (3:40–4:00)

1. Scroll back to the landing page's architecture diagram one more time.
2. Close on: *"Everything marked LIVE in this diagram is what you just saw
   running — governance, semantic memory, tool-calling, and a real agent
   registry. Everything marked PLANNED is scoped in the roadmap with no
   overclaiming."*

---

## Reference: real outputs from this codebase (for your own verification)

These came from the actual running instance while building this script —
useful if you want to sanity-check your own recording matches real behavior:

```
POST /v1/prompt {"agent_id": "<math-tutor-id>", "prompt": "What is 128 times 37?"}
→ "The result of multiplying 128 by 37 is 4736."
  tool_calls: [{"name": "calculate", "arguments": {"expression": "128*37"}, "result": "4736"}]

POST /v1/prompt {"agent_id": "<math-tutor-id>", "prompt": "What is 65 times 12?"}
→ "The result of multiplying 65 by 12 is 780."
  tool_calls: [{"name": "calculate", "arguments": {"expression": "65 * 12"}, "result": "780"}]

POST /v1/prompt {"agent_id": "<math-tutor-id>", "prompt": "What is 47 times 89?"}
→ "The result of multiplying 47 by 89 is 4183."
  tool_calls: [{"name": "calculate", "arguments": {"expression": "47 * 89"}, "result": "4183"}]
```

All three are mathematically correct (128×37=4736, 65×12=780, 47×89=4183) —
the tool actually computed them; the model didn't guess.
