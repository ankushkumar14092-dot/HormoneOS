"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Patient, TimelineRow, CompareResult } from "@/types";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";

function MiniChart({ rows, color, label }: { rows: TimelineRow[]; color: string; label: string }) {
  const data = rows.map((r) => ({
    day: r.day_in_study ?? 0,
    est: r.hormones?.estrogen_pg_ml ?? null,
    hr:  r.wearables?.heart_rate_bpm ?? null,
  }));
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
      <p className="text-xs text-zinc-500 mb-3">{label}</p>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={data}>
          <XAxis dataKey="day" tick={{ fontSize: 9, fill: "#71717a" }} />
          <YAxis tick={{ fontSize: 9, fill: "#71717a" }} />
          <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", fontSize: 10 }} />
          <Legend wrapperStyle={{ fontSize: 10 }} />
          <Line type="monotone" dataKey="est" name="Estrogen" stroke={color}       dot={false} strokeWidth={1.5} connectNulls />
          <Line type="monotone" dataKey="hr"  name="Heart Rate" stroke="#71717a"   dot={false} strokeWidth={1}   connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function ComparePage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [a, setA]               = useState<number | null>(null);
  const [b, setB]               = useState<number | null>(null);
  const [rowsA, setRowsA]       = useState<TimelineRow[]>([]);
  const [rowsB, setRowsB]       = useState<TimelineRow[]>([]);
  const [result, setResult]     = useState<CompareResult | null>(null);
  const [loading, setLoading]   = useState(false);

  useEffect(() => {
    api.patients().then((p) => {
      setPatients(p);
      if (p.length >= 2) { setA(p[0].id); setB(p[1].id); }
    });
  }, []);

  useEffect(() => { if (a) api.timeline(a).then(setRowsA); }, [a]);
  useEffect(() => { if (b) api.timeline(b).then(setRowsB); }, [b]);

  async function runCompare() {
    if (!a || !b) return;
    setLoading(true);
    try { setResult(await api.compare(a, b)); }
    finally { setLoading(false); }
  }

  const scoreColor = result
    ? result.similarity_score >= 0.7 ? "text-emerald-400"
    : result.similarity_score >= 0.4 ? "text-amber-400"
    : "text-red-400"
    : "";

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-zinc-100 font-sans tracking-tight">Representation Comparison</h1>
        <p className="text-sm text-zinc-500 mt-1">Compute alignment distance and similarity between subject embeddings</p>
      </div>

      {/* Selectors */}
      <div className="flex items-center gap-4 flex-wrap">
        {[{ label: "Subject A", val: a, set: setA, color: "#a78bfa" },
          { label: "Subject B", val: b, set: setB, color: "#34d399" }].map(({ label, val, set, color }) => (
          <div key={label} className="flex items-center gap-2">
            <span className="text-xs text-zinc-500">{label}</span>
            <select
              className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm text-zinc-200"
              value={val ?? ""}
              onChange={(e) => set(Number(e.target.value))}
            >
              {patients.map((p) => <option key={p.id} value={p.id}>Subject #{p.id}</option>)}
            </select>
          </div>
        ))}
        <button
          onClick={runCompare}
          disabled={loading || !a || !b || a === b}
          className="px-4 py-1.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 rounded-lg text-sm text-white transition-colors"
        >
          {loading ? "Comparing…" : "Compare"}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
          <div className="grid grid-cols-3 gap-6">
            <div>
              <p className="text-xs text-zinc-500 mb-1">Embedding Similarity Score</p>
              <p className={`text-3xl font-bold ${scoreColor}`}>{(result.similarity_score * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-xs text-zinc-500 mb-1">Cosine Similarity</p>
              <p className="text-xl font-semibold text-zinc-200">{result.cosine_similarity.toFixed(4)}</p>
            </div>
            <div>
              <p className="text-xs text-zinc-500 mb-1">DTW Sequence Distance</p>
              <p className="text-xl font-semibold text-zinc-200">{result.dtw_distance.toFixed(2)}</p>
            </div>
          </div>
          {result.narrative && (
            <div className="border-t border-zinc-800 pt-4 space-y-2">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 border-b border-zinc-800/50 pb-2">
                <p className="text-xs text-zinc-400 font-semibold uppercase tracking-widest">Research Interpretation</p>
                <span className="text-[10px] text-zinc-500 italic">
                  *The LLM is not making clinical decisions; it translates model outputs into human-readable research summaries.
                </span>
              </div>
              <p className="text-sm text-zinc-300 leading-relaxed">{result.narrative}</p>
            </div>
          )}
        </div>
      )}

      {/* Split-screen timelines */}
      <div className="grid md:grid-cols-2 gap-4">
        <MiniChart rows={rowsA} color="#a78bfa" label={`Subject A (#${a})`} />
        <MiniChart rows={rowsB} color="#34d399" label={`Subject B (#${b})`} />
      </div>
    </div>
  );
}
