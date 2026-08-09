"use client";

import { useEffect, useState } from "react";

const GATEWAY_URL = process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:8000";

type HealthStatus = { status: string; service: string } | null;

export default function Home() {
  const [health, setHealth] = useState<HealthStatus>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${GATEWAY_URL}/health`)
      .then((res) => res.json())
      .then(setHealth)
      .catch((err) => setError(String(err)));
  }, []);

  return (
    <main className="max-w-2xl mx-auto py-16 px-6">
      <h1 className="text-3xl font-semibold mb-2">AgentOS</h1>
      <p className="text-slate-400 mb-8">L0 Dashboard Console</p>

      <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-sm uppercase tracking-wide text-slate-500 mb-2">Govrix Gateway</h2>
        {error && <p className="text-red-400">Unreachable: {error}</p>}
        {!error && !health && <p className="text-slate-400">Checking…</p>}
        {health && (
          <p className="text-emerald-400">
            {health.service} — {health.status}
          </p>
        )}
      </div>
    </main>
  );
}
