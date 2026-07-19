"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import type { BenchmarkResult } from "@/types";

const TASKS = [
  { id: "phase_classification", label: "Downstream Task: Menstrual Phase Classification", desc: "Evaluate HSF representation accuracy on predicting biological cycle phases" },
  { id: "hormone_regression",   label: "Downstream Task: Estrogen Level Regression",   desc: "Evaluate HSF representation accuracy on predicting absolute estrogen levels" },
];

export default function BenchmarkPage() {
  const [results, setResults]   = useState<Record<string, BenchmarkResult>>({});
  const [running, setRunning]   = useState<string | null>(null);

  async function run(task: string) {
    setRunning(task);
    try {
      const r = await api.benchmark(task);
      setResults((prev) => ({ ...prev, [task]: r }));
    } finally {
      setRunning(null);
    }
  }

  function downloadEmbeddings(fmt: "json" | "csv") {
    window.open(`http://localhost:8000/api/v1/registry/download?fmt=${fmt}`, "_blank");
  }

  return (
    <div className="max-w-3xl space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-zinc-100 font-sans tracking-tight">Benchmark Center</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Validate HSF representations against downstream clinical prediction tasks and export registry records
        </p>
      </div>

      {/* Tasks */}
      <div className="space-y-4">
        {TASKS.map(({ id, label, desc }) => {
          const r = results[id];
          return (
            <div key={id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex items-start justify-between gap-4">
              <div className="space-y-1 flex-1">
                <p className="text-sm font-medium text-zinc-200">{label}</p>
                <p className="text-xs text-zinc-500">{desc}</p>
                {r && (
                  <div className="flex gap-4 mt-3">
                    {r.accuracy != null && (
                      <div>
                        <p className="text-[10px] text-zinc-600">Accuracy</p>
                        <p className="text-lg font-semibold text-emerald-400">{(r.accuracy * 100).toFixed(1)}%</p>
                      </div>
                    )}
                    {r.rmse != null && (
                      <div>
                        <p className="text-[10px] text-zinc-600">RMSE</p>
                        <p className="text-lg font-semibold text-amber-400">{r.rmse.toFixed(2)}</p>
                      </div>
                    )}
                    {r.details?.n_samples != null && (
                      <div>
                        <p className="text-[10px] text-zinc-600">Samples</p>
                        <p className="text-lg font-semibold text-zinc-300">{String(r.details.n_samples)}</p>
                      </div>
                    )}
                    {r.details?.error != null && (
                      <p className="text-xs text-red-400">{String(r.details.error as string)}</p>
                    )}
                  </div>
                )}
              </div>
              <button
                onClick={() => run(id)}
                disabled={running === id}
                className="shrink-0 px-4 py-1.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 rounded-lg text-sm text-white transition-colors"
              >
                {running === id ? "Running…" : "Run Evaluation"}
              </button>
            </div>
          );
        })}
      </div>

      {/* Download */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-3">
        <p className="text-sm font-medium text-zinc-200">Download Stored HSF Representations</p>
        <p className="text-xs text-zinc-500">Export all stored patient embeddings for use in external research models</p>
        <div className="flex gap-3">
          <button
            onClick={() => downloadEmbeddings("json")}
            className="px-4 py-1.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-sm text-zinc-300 transition-colors"
          >
            Download JSON
          </button>
          <button
            onClick={() => downloadEmbeddings("csv")}
            className="px-4 py-1.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-sm text-zinc-300 transition-colors"
          >
            Download CSV
          </button>
        </div>
      </div>

      {/* API Playground */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-3">
        <p className="text-sm font-medium text-zinc-200">Research API Playground</p>
        <p className="text-xs text-zinc-500">Explore and test open research infrastructure APIs via interactive Swagger UI</p>
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noreferrer"
          className="inline-block px-4 py-1.5 bg-sky-900/50 hover:bg-sky-800/50 border border-sky-700/50 rounded-lg text-sm text-sky-300 transition-colors"
        >
          Open Swagger UI →
        </a>
      </div>
    </div>
  );
}
