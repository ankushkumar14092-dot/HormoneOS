"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Patient, TimelineRow } from "@/types";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from "recharts";

const PHASE_COLORS: Record<string, string> = {
  menstrual: "#f43f5e", follicular: "#a78bfa",
  ovulatory: "#34d399",  luteal: "#fb923c", unknown: "#6b7280",
};

export default function TimelinePage() {
  const [patients, setPatients]   = useState<Patient[]>([]);
  const [selected, setSelected]   = useState<number | null>(null);
  const [rows, setRows]           = useState<TimelineRow[]>([]);
  const [loading, setLoading]     = useState(false);

  useEffect(() => {
    api.patients().then((p) => { setPatients(p); if (p.length) setSelected(p[0].id); });
  }, []);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    api.timeline(selected).then(setRows).finally(() => setLoading(false));
  }, [selected]);

  const chartData = rows.map((r) => ({
    day:   r.day_in_study ?? 0,
    hr:    r.wearables?.heart_rate_bpm ?? null,
    vo2:   r.wearables?.vo2_max ?? null,
    temp:  r.wearables?.computed_temperature_c ?? null,
    est:   r.hormones?.estrogen_pg_ml ?? null,
    prog:  r.hormones?.progesterone_ng_ml ?? null,
    lh:    r.hormones?.lh_miu_ml ?? null,
    gluc:  r.glucose?.glucose_mg_dl ?? null,
  }));

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-zinc-100 font-sans tracking-tight">Longitudinal Signals</h1>
        <p className="text-sm text-zinc-500 mt-1">Multi-modal patient sensor telemetry and clinical observations</p>
      </div>

      {/* Subject selector */}
      <div className="flex items-center gap-3">
        <label className="text-xs text-zinc-500">Subject ID</label>
        <select
          className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm text-zinc-200"
          value={selected ?? ""}
          onChange={(e) => setSelected(Number(e.target.value))}
        >
          {patients.map((p) => (
            <option key={p.id} value={p.id}>Subject #{p.id}</option>
          ))}
        </select>
        {loading && <span className="text-xs text-zinc-600">Loading…</span>}
      </div>

      {chartData.length > 0 && (
        <div className="space-y-6">
          {/* Wearables chart */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
            <p className="text-xs text-zinc-500 mb-4 uppercase tracking-widest">Wearables</p>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={chartData}>
                <XAxis dataKey="day" tick={{ fontSize: 10, fill: "#71717a" }} label={{ value: "Day", position: "insideBottomRight", offset: -5, fontSize: 10, fill: "#71717a" }} />
                <YAxis tick={{ fontSize: 10, fill: "#71717a" }} />
                <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", fontSize: 11 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="hr"   name="Heart Rate (bpm)"  stroke="#a78bfa" dot={false} strokeWidth={1.5} connectNulls />
                <Line type="monotone" dataKey="vo2"  name="VO2 Max"           stroke="#34d399" dot={false} strokeWidth={1.5} connectNulls />
                <Line type="monotone" dataKey="temp" name="Temperature (°C)"  stroke="#fb923c" dot={false} strokeWidth={1.5} connectNulls />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Hormones chart */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
            <p className="text-xs text-zinc-500 mb-4 uppercase tracking-widest">Hormones</p>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={chartData}>
                <XAxis dataKey="day" tick={{ fontSize: 10, fill: "#71717a" }} />
                <YAxis tick={{ fontSize: 10, fill: "#71717a" }} />
                <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", fontSize: 11 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="est"  name="Estrogen (pg/mL)"      stroke="#f472b6" dot={false} strokeWidth={1.5} connectNulls />
                <Line type="monotone" dataKey="prog" name="Progesterone (ng/mL)"  stroke="#818cf8" dot={false} strokeWidth={1.5} connectNulls />
                <Line type="monotone" dataKey="lh"   name="LH (mIU/mL)"          stroke="#fbbf24" dot={false} strokeWidth={1.5} connectNulls />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Glucose chart */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
            <p className="text-xs text-zinc-500 mb-4 uppercase tracking-widest">Glucose</p>
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={chartData}>
                <XAxis dataKey="day" tick={{ fontSize: 10, fill: "#71717a" }} />
                <YAxis tick={{ fontSize: 10, fill: "#71717a" }} />
                <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", fontSize: 11 }} />
                <ReferenceLine y={5.6} stroke="#f43f5e" strokeDasharray="3 3" label={{ value: "High", fontSize: 9, fill: "#f43f5e" }} />
                <Line type="monotone" dataKey="gluc" name="Glucose (mmol/L)" stroke="#22d3ee" dot={false} strokeWidth={1.5} connectNulls />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {!loading && chartData.length === 0 && selected && (
        <p className="text-sm text-zinc-600">No timeline data found for this subject. Ensure the database is populated.</p>
      )}
    </div>
  );
}
