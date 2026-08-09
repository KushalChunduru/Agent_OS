"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const GATEWAY_URL = process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:8000";

type GatewayState = "checking" | "online" | "offline";

type Layer = {
  code: string;
  name: string;
  desc: string;
  status: "live" | "stub" | "planned";
};

const layers: Layer[] = [
  { code: "L0", name: "Dashboard Console", desc: "Agent management, live monitoring, this UI.", status: "live" },
  { code: "L1", name: "Govrix Scout", desc: "Governance & security — auth, rate limits, policy checks, audit log. Nothing bypasses this layer.", status: "live" },
  { code: "L2A", name: "MemoryMesh", desc: "Persistent memory — store, list, semantic search.", status: "live" },
  { code: "L2B", name: "InferCraft", desc: "Model routing — Anthropic, OpenAI, or local Ollama, chosen automatically.", status: "live" },
  { code: "L2C", name: "SkillForge", desc: "Mines repeated workflows into reusable skills.", status: "planned" },
  { code: "L2E", name: "EvolveCraft", desc: "Self-improvement loop — proposes changes, never auto-applies them.", status: "planned" },
  { code: "L3", name: "Storage", desc: "SQLite today; Postgres/pgvector, Qdrant, Neo4j as it scales.", status: "stub" },
  { code: "L4", name: "Observability", desc: "Prometheus, Grafana, RAGAS, Locust.", status: "planned" },
];

const statusStyle: Record<Layer["status"], { label: string; dot: string; text: string }> = {
  live: { label: "LIVE", dot: "bg-[--accent]", text: "text-[--accent]" },
  stub: { label: "STUB", dot: "bg-[--accent-2]", text: "text-[--accent-2]" },
  planned: { label: "PLANNED", dot: "bg-slate-600", text: "text-slate-500" },
};

function StatusPill({ status }: { status: Layer["status"] }) {
  const s = statusStyle[status];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border border-[--border-strong] px-2 py-0.5 font-mono-tech text-[10px] tracking-widest ${s.text}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} />
      {s.label}
    </span>
  );
}

const features = [
  {
    title: "Governance first",
    desc: "Every request — from dashboard, agent, or API — passes through Govrix before it reaches an LLM. Auth, rate limits, and policy checks are not optional middleware, they're the front door.",
  },
  {
    title: "Persistent memory",
    desc: "MemoryMesh gives agents working, episodic, and semantic memory that survives across sessions, with a storage interface designed to swap SQLite for a real vector DB without touching callers.",
  },
  {
    title: "Model-agnostic inference",
    desc: "InferCraft routes each prompt to whichever provider is configured — Anthropic, OpenAI, or a local Ollama model — escalating model tier automatically on longer, harder prompts.",
  },
  {
    title: "Human-gated evolution",
    desc: "EvolveCraft (planned) watches latency, cost, and quality, and proposes changes as a diff. It never applies them itself — a human always reviews first.",
  },
];

const stack = [
  "FastAPI", "Next.js", "TailwindCSS", "SQLite", "Ollama",
  "Anthropic", "OpenAI", "Docker Compose", "Redis",
];

export default function Landing() {
  const [gateway, setGateway] = useState<GatewayState>("checking");

  useEffect(() => {
    fetch(`${GATEWAY_URL}/health`)
      .then((res) => (res.ok ? setGateway("online") : setGateway("offline")))
      .catch(() => setGateway("offline"));
  }, []);

  return (
    <main className="min-h-screen">
      {/* Nav */}
      <header className="sticky top-0 z-10 border-b border-[--border] bg-[--bg]/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="font-mono-tech text-sm tracking-widest text-[--muted]">
            <span className="text-[--text]">[</span>AGENT<span className="text-accent">OS</span><span className="text-[--text]">]</span>
          </div>
          <nav className="hidden items-center gap-8 font-mono-tech text-xs uppercase tracking-widest text-[--muted] sm:flex">
            <a href="#architecture" className="hover:text-[--text]">Architecture</a>
            <a href="#features" className="hover:text-[--text]">Capabilities</a>
            <a
              href="https://github.com/KushalChunduru/Agent_OS"
              target="_blank"
              rel="noreferrer"
              className="hover:text-[--text]"
            >
              GitHub
            </a>
          </nav>
          <Link
            href="/console"
            className="rounded border border-[--accent] bg-[--accent-dim] px-4 py-2 font-mono-tech text-xs uppercase tracking-widest text-[--accent] hover:bg-[--accent]/20"
          >
            Open Console →
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-6xl px-6 pt-20 pb-16">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[--border-strong] px-3 py-1 font-mono-tech text-[11px] uppercase tracking-widest text-[--muted]">
          <span
            className={`h-1.5 w-1.5 rounded-full status-dot ${
              gateway === "online" ? "bg-[--accent]" : gateway === "offline" ? "bg-red-500" : "bg-slate-500"
            }`}
          />
          Govrix Gateway — {gateway === "checking" ? "checking…" : gateway}
        </div>

        <h1 className="max-w-3xl font-display text-4xl font-medium leading-tight tracking-tight text-[--text] sm:text-5xl">
          A self-hosted operating system for autonomous AI agents.
        </h1>
        <p className="mt-6 max-w-2xl text-lg leading-relaxed text-[--muted]">
          Not another chatbot wrapper. AgentOS is infrastructure — governance, memory,
          inference routing, and observability run as isolated services, the same way
          AWS gives cloud apps compute, storage, and networking as separate primitives.
        </p>

        <div className="mt-8 flex flex-wrap gap-4">
          <Link
            href="/console"
            className="rounded bg-[--accent] px-5 py-3 font-mono-tech text-sm font-medium uppercase tracking-widest text-[--bg] hover:opacity-90"
          >
            Open Console
          </Link>
          <a
            href="https://github.com/KushalChunduru/Agent_OS"
            target="_blank"
            rel="noreferrer"
            className="rounded border border-[--border-strong] px-5 py-3 font-mono-tech text-sm uppercase tracking-widest text-[--text] hover:border-[--muted]"
          >
            View Source
          </a>
        </div>
      </section>

      {/* Architecture */}
      <section id="architecture" className="mx-auto max-w-6xl px-6 py-16">
        <div className="mb-10 flex items-baseline justify-between">
          <h2 className="font-display text-2xl font-medium text-[--text]">Layered architecture</h2>
          <span className="font-mono-tech text-xs uppercase tracking-widest text-[--muted]">
            request flows top → bottom
          </span>
        </div>

        <div className="relative">
          <div className="absolute left-[27px] top-3 bottom-3 w-px bg-[--border-strong] sm:left-[35px]" aria-hidden />
          <div className="space-y-3">
            {layers.map((layer) => (
              <div key={layer.code} className="relative flex items-start gap-4 pl-2 sm:gap-6">
                <div className="relative z-[1] flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-[--border-strong] bg-[--bg-panel] font-mono-tech text-[10px] text-[--muted] sm:h-14 sm:w-14 sm:text-xs">
                  {layer.code}
                </div>
                <div className="panel flex-1 rounded-lg px-4 py-3 sm:px-5 sm:py-4">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="font-display text-base font-medium text-[--text] sm:text-lg">{layer.name}</h3>
                    <StatusPill status={layer.status} />
                  </div>
                  <p className="mt-1 text-sm leading-relaxed text-[--muted]">{layer.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="mb-10 font-display text-2xl font-medium text-[--text]">Capabilities</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {features.map((f) => (
            <div key={f.title} className="panel rounded-lg p-6">
              <h3 className="font-display text-lg font-medium text-[--text]">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-[--muted]">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Stack */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="mb-6 font-mono-tech text-xs uppercase tracking-widest text-[--muted]">Built with</h2>
        <div className="flex flex-wrap gap-2">
          {stack.map((s) => (
            <span
              key={s}
              className="rounded border border-[--border-strong] px-3 py-1.5 font-mono-tech text-xs text-[--muted]"
            >
              {s}
            </span>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[--border]">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-4 px-6 py-8 sm:flex-row sm:items-center">
          <p className="font-mono-tech text-xs text-[--muted]">
            AgentOS — Phase 1 MVP. See the{" "}
            <a
              href="https://github.com/KushalChunduru/Agent_OS/blob/main/docs/ROADMAP.md"
              target="_blank"
              rel="noreferrer"
              className="text-accent hover:underline"
            >
              roadmap
            </a>{" "}
            for what&apos;s next.
          </p>
          <Link href="/console" className="font-mono-tech text-xs text-accent hover:underline">
            Open Console →
          </Link>
        </div>
      </footer>
    </main>
  );
}
