"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const GATEWAY_URL = process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:8000";

type HealthStatus = { status: string; service: string } | null;

type ToolCall = { name: string; arguments: Record<string, unknown>; result: string };

type PromptResponse = {
  agent_id: string;
  user: string;
  response: string;
  provider: string;
  model: string;
  memories_used: number;
  tool_calls: ToolCall[];
};

type ChatMessage = {
  role: "user" | "agent" | "error";
  text: string;
  meta?: string;
  toolCalls?: ToolCall[];
};

type Memory = {
  id: string;
  agent_id: string;
  kind: string;
  content: string;
};

type Agent = {
  id: string;
  name: string;
  system_prompt: string | null;
  model_tier: string;
};

function RoleBadge({ role }: { role: ChatMessage["role"] }) {
  const label = role === "user" ? "YOU" : role === "agent" ? "AGENT" : "ERROR";
  const color =
    role === "user" ? "text-[--accent-2]" : role === "agent" ? "text-[--accent]" : "text-red-400";
  return <span className={`font-mono-tech text-[10px] tracking-widest ${color}`}>{label}</span>;
}

function formatToolCall(tc: ToolCall): string {
  const args = Object.values(tc.arguments).map(String).join(", ");
  return `🔧 ${tc.name}(${args}) → ${tc.result}`;
}

export default function Console() {
  const [health, setHealth] = useState<HealthStatus>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  const [agents, setAgents] = useState<Agent[]>([]);
  const [agentId, setAgentId] = useState("demo");
  const [showNewAgentForm, setShowNewAgentForm] = useState(false);
  const [newAgentName, setNewAgentName] = useState("");
  const [newAgentPrompt, setNewAgentPrompt] = useState("");
  const [newAgentTier, setNewAgentTier] = useState<"small" | "large" | "reasoning">("small");
  const [creatingAgent, setCreatingAgent] = useState(false);

  const [prompt, setPrompt] = useState("");
  const [sending, setSending] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const [memories, setMemories] = useState<Memory[]>([]);
  const [memoriesError, setMemoriesError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${GATEWAY_URL}/health`)
      .then((res) => res.json())
      .then(setHealth)
      .catch((err) => setHealthError(String(err)));
    refreshAgents();
  }, []);

  async function refreshAgents() {
    try {
      const res = await fetch(`${GATEWAY_URL}/v1/agents`);
      const data = await res.json();
      if (Array.isArray(data)) setAgents(data);
    } catch {
      // Registry is best-effort for the picker; the plain-text "demo" agent still works either way.
    }
  }

  async function createAgent() {
    if (!newAgentName.trim() || creatingAgent) return;
    setCreatingAgent(true);
    try {
      const res = await fetch(`${GATEWAY_URL}/v1/agents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newAgentName,
          system_prompt: newAgentPrompt || null,
          model_tier: newAgentTier,
        }),
      });
      const agent: Agent = await res.json();
      setAgents((prev) => [agent, ...prev]);
      setAgentId(agent.id);
      setNewAgentName("");
      setNewAgentPrompt("");
      setNewAgentTier("small");
      setShowNewAgentForm(false);
    } finally {
      setCreatingAgent(false);
    }
  }

  async function refreshMemories() {
    setMemoriesError(null);
    try {
      const res = await fetch(`${GATEWAY_URL}/v1/memory/${encodeURIComponent(agentId)}`);
      const data = await res.json();
      if (Array.isArray(data)) {
        setMemories(data);
      } else {
        setMemoriesError(data.error ?? "Unexpected response");
      }
    } catch (err) {
      setMemoriesError(String(err));
    }
  }

  async function sendPrompt() {
    if (!prompt.trim() || sending) return;
    const userText = prompt;
    setMessages((prev) => [...prev, { role: "user", text: userText }]);
    setPrompt("");
    setSending(true);

    try {
      const res = await fetch(`${GATEWAY_URL}/v1/prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId, prompt: userText }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        setMessages((prev) => [...prev, { role: "error", text: err.detail ?? "Request failed" }]);
        return;
      }
      const data: PromptResponse = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          text: data.response,
          meta: `${data.provider}/${data.model} · ${data.memories_used} memories used`,
          toolCalls: data.tool_calls,
        },
      ]);
      refreshMemories();
    } catch (err) {
      setMessages((prev) => [...prev, { role: "error", text: String(err) }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-[--border] bg-[--bg]/85 backdrop-blur">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
          <Link href="/" className="font-mono-tech text-sm tracking-widest text-[--muted] hover:text-[--text]">
            <span className="text-[--text]">[</span>AGENT<span className="text-accent">OS</span><span className="text-[--text]">]</span>
          </Link>
          <div className="flex items-center gap-2 font-mono-tech text-[11px] uppercase tracking-widest text-[--muted]">
            <span
              className={`h-1.5 w-1.5 rounded-full status-dot ${
                healthError ? "bg-red-500" : health ? "bg-[--accent]" : "bg-slate-500"
              }`}
            />
            {healthError ? "gateway offline" : health ? "govrix online" : "checking…"}
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-4xl space-y-6 px-6 py-10">
        <div>
          <h1 className="font-display text-2xl font-medium text-[--text]">Agent Console</h1>
          <p className="mt-1 text-sm text-[--muted]">
            L0 — talk to an agent through Govrix; every turn is retrieved from and written back to
            MemoryMesh. Agents can call tools (calculator, current time) via InferCraft.
          </p>
        </div>

        <div className="panel rounded-lg p-5 space-y-3">
          <div className="flex items-center gap-3">
            <label className="font-mono-tech text-xs uppercase tracking-widest text-[--muted] shrink-0">
              Agent
            </label>
            <select
              value={agentId}
              onChange={(e) => setAgentId(e.target.value)}
              className="flex-1 rounded border border-[--border-strong] bg-[--bg] px-3 py-1.5 text-sm text-[--text] outline-none focus:border-[--accent]"
            >
              <option value="demo">demo (ad-hoc)</option>
              {agents.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} · {a.model_tier}
                </option>
              ))}
            </select>
            <button
              onClick={refreshMemories}
              className="rounded border border-[--border-strong] px-3 py-1.5 font-mono-tech text-xs uppercase tracking-widest text-[--muted] hover:border-[--muted] hover:text-[--text]"
            >
              Load memories
            </button>
            <button
              onClick={() => setShowNewAgentForm((v) => !v)}
              className="rounded border border-[--border-strong] px-3 py-1.5 font-mono-tech text-xs uppercase tracking-widest text-[--muted] hover:border-[--muted] hover:text-[--text]"
            >
              {showNewAgentForm ? "Cancel" : "+ New agent"}
            </button>
          </div>

          {showNewAgentForm && (
            <div className="space-y-2 border-t border-[--border] pt-3">
              <input
                value={newAgentName}
                onChange={(e) => setNewAgentName(e.target.value)}
                placeholder="Agent name"
                className="w-full rounded border border-[--border-strong] bg-[--bg] px-3 py-1.5 text-sm text-[--text] outline-none focus:border-[--accent]"
              />
              <textarea
                value={newAgentPrompt}
                onChange={(e) => setNewAgentPrompt(e.target.value)}
                placeholder="System prompt (optional) — defines this agent's persona"
                rows={2}
                className="w-full resize-none rounded border border-[--border-strong] bg-[--bg] px-3 py-1.5 text-sm text-[--text] outline-none focus:border-[--accent]"
              />
              <div className="flex items-center gap-3">
                <select
                  value={newAgentTier}
                  onChange={(e) => setNewAgentTier(e.target.value as typeof newAgentTier)}
                  className="rounded border border-[--border-strong] bg-[--bg] px-3 py-1.5 text-sm text-[--text] outline-none focus:border-[--accent]"
                >
                  <option value="small">small</option>
                  <option value="large">large</option>
                  <option value="reasoning">reasoning</option>
                </select>
                <button
                  onClick={createAgent}
                  disabled={creatingAgent || !newAgentName.trim()}
                  className="rounded bg-[--accent] px-4 py-1.5 font-mono-tech text-xs font-medium uppercase tracking-widest text-[--bg] hover:opacity-90 disabled:opacity-40"
                >
                  {creatingAgent ? "Creating…" : "Create"}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="panel rounded-lg p-5">
          <div className="h-80 overflow-y-auto rounded border border-[--border] bg-[--bg] p-4 space-y-4">
            {messages.length === 0 && (
              <p className="font-mono-tech text-xs text-[--muted]">No messages yet — ask something below.</p>
            )}
            {messages.map((m, i) => (
              <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
                <div className="mb-1">
                  <RoleBadge role={m.role} />
                </div>
                <div
                  className={
                    "inline-block rounded-lg px-3 py-2 text-sm max-w-[85%] text-left " +
                    (m.role === "user"
                      ? "panel-raised text-[--text]"
                      : m.role === "error"
                        ? "border border-red-900 bg-red-950/60 text-red-300"
                        : "border border-[--accent-dim] bg-[--accent-dim]/20 text-[--text]")
                  }
                >
                  {m.text}
                  {m.toolCalls && m.toolCalls.length > 0 && (
                    <div className="mt-1.5 space-y-0.5 border-t border-[--border] pt-1.5">
                      {m.toolCalls.map((tc, j) => (
                        <div key={j} className="font-mono-tech text-[10px] text-[--accent-2]">
                          {formatToolCall(tc)}
                        </div>
                      ))}
                    </div>
                  )}
                  {m.meta && (
                    <div className="mt-1.5 font-mono-tech text-[10px] text-[--muted]">{m.meta}</div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 flex gap-2">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendPrompt();
                }
              }}
              placeholder="Ask the agent something…"
              rows={2}
              className="flex-1 resize-none rounded border border-[--border-strong] bg-[--bg] px-3 py-2 text-sm text-[--text] outline-none focus:border-[--accent]"
            />
            <button
              onClick={sendPrompt}
              disabled={sending}
              className="rounded bg-[--accent] px-5 font-mono-tech text-xs font-medium uppercase tracking-widest text-[--bg] hover:opacity-90 disabled:opacity-40"
            >
              {sending ? "Sending…" : "Send"}
            </button>
          </div>
        </div>

        <div className="panel rounded-lg p-5">
          <h2 className="mb-3 font-mono-tech text-xs uppercase tracking-widest text-[--muted]">
            MemoryMesh — {agentId}
          </h2>
          {memoriesError && <p className="text-sm text-red-400">{memoriesError}</p>}
          {!memoriesError && memories.length === 0 && (
            <p className="font-mono-tech text-xs text-[--muted]">No memories loaded yet.</p>
          )}
          <ul className="space-y-2.5">
            {memories.map((m) => (
              <li key={m.id} className="border-b border-[--border] pb-2.5 text-sm text-[--text] last:border-0">
                <span className="mr-2 font-mono-tech text-[10px] uppercase tracking-widest text-[--muted]">
                  {m.kind}
                </span>
                {m.content}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </main>
  );
}
