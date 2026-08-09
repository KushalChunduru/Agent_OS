"use client";

import { useEffect, useState } from "react";

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

export default function Home() {
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
    <main className="max-w-3xl mx-auto py-16 px-6 space-y-6">
      <div>
        <h1 className="text-3xl font-semibold mb-2">AgentOS</h1>
        <p className="text-slate-400">L0 Dashboard Console</p>
      </div>

      <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-sm uppercase tracking-wide text-slate-500 mb-2">Govrix Gateway</h2>
        {healthError && <p className="text-red-400">Unreachable: {healthError}</p>}
        {!healthError && !health && <p className="text-slate-400">Checking…</p>}
        {health && (
          <p className="text-emerald-400">
            {health.service} — {health.status}
          </p>
        )}
      </div>

      <div className="rounded-lg border border-slate-800 bg-slate-900 p-6 space-y-4">
        <h2 className="text-sm uppercase tracking-wide text-slate-500">Agent Console</h2>

        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-400 shrink-0">Agent ID</label>
          <input
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
            className="flex-1 rounded border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm"
          />
          <button
            onClick={refreshMemories}
            className="rounded border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800"
          >
            Load memories
          </button>
        </div>

        <div className="h-72 overflow-y-auto rounded border border-slate-800 bg-slate-950 p-3 space-y-3">
          {messages.length === 0 && <p className="text-slate-500 text-sm">No messages yet.</p>}
          {messages.map((m, i) => (
            <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
              <div
                className={
                  "inline-block rounded-lg px-3 py-2 text-sm max-w-[85%] " +
                  (m.role === "user"
                    ? "bg-sky-900 text-sky-50"
                    : m.role === "error"
                      ? "bg-red-950 text-red-300"
                      : "bg-slate-800 text-slate-100")
                }
              >
                {m.text}
                {m.meta && <div className="mt-1 text-xs text-slate-400">{m.meta}</div>}
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-2">
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
            className="flex-1 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm resize-none"
          />
          <button
            onClick={sendPrompt}
            disabled={sending}
            className="rounded bg-sky-700 px-4 py-2 text-sm font-medium text-white hover:bg-sky-600 disabled:opacity-50"
          >
            {sending ? "Sending…" : "Send"}
          </button>
        </div>
      </div>

      <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-sm uppercase tracking-wide text-slate-500 mb-2">MemoryMesh — {agentId}</h2>
        {memoriesError && <p className="text-red-400 text-sm">{memoriesError}</p>}
        {!memoriesError && memories.length === 0 && (
          <p className="text-slate-500 text-sm">No memories loaded yet.</p>
        )}
        <ul className="space-y-2">
          {memories.map((m) => (
            <li key={m.id} className="text-sm text-slate-300 border-b border-slate-800 pb-2 last:border-0">
              <span className="text-xs uppercase text-slate-500 mr-2">{m.kind}</span>
              {m.content}
            </li>
          ))}
        </ul>
      </div>
    </main>
  );
}
