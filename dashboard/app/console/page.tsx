"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const GATEWAY_URL = process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:8000";

type HealthStatus = { status: string; service: string } | null;

type PromptResponse = {
  agent_id: string;
  user: string;
  response: string;
  provider: string;
  model: string;
  memories_used: number;
};

type ChatMessage = {
  role: "user" | "agent" | "error";
  text: string;
  meta?: string;
};

type Memory = {
  id: string;
  agent_id: string;
  kind: string;
  content: string;
};

function RoleBadge({ role }: { role: ChatMessage["role"] }) {
  const label = role === "user" ? "YOU" : role === "agent" ? "AGENT" : "ERROR";
  const color =
    role === "user" ? "text-[--accent-2]" : role === "agent" ? "text-[--accent]" : "text-red-400";
  return <span className={`font-mono-tech text-[10px] tracking-widest ${color}`}>{label}</span>;
}

export default function Console() {
  const [health, setHealth] = useState<HealthStatus>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  const [agentId, setAgentId] = useState("demo");
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
  }, []);

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
            L0 — talk to an agent through Govrix; every turn is retrieved from and written back to MemoryMesh.
          </p>
        </div>

        <div className="panel rounded-lg p-5">
          <div className="flex items-center gap-3">
            <label className="font-mono-tech text-xs uppercase tracking-widest text-[--muted] shrink-0">
              Agent ID
            </label>
            <input
              value={agentId}
              onChange={(e) => setAgentId(e.target.value)}
              className="flex-1 rounded border border-[--border-strong] bg-[--bg] px-3 py-1.5 text-sm text-[--text] outline-none focus:border-[--accent]"
            />
            <button
              onClick={refreshMemories}
              className="rounded border border-[--border-strong] px-3 py-1.5 font-mono-tech text-xs uppercase tracking-widest text-[--muted] hover:border-[--muted] hover:text-[--text]"
            >
              Load memories
            </button>
          </div>
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
