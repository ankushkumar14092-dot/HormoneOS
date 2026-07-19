"use client";
import { useEffect, useState, useMemo } from "react";
import { api } from "@/lib/api";
import type { EmbeddingRecord, Dataset } from "@/types";
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

// Corrected 2-component PCA via covariance power iteration (runs client-side, no sklearn needed)
function pca2d(vectors: number[][]): [number, number][] {
  const n = vectors.length;
  if (n === 0) return [];
  const d = vectors[0].length;
  const mean = Array.from({ length: d }, (_, j) => vectors.reduce((s, v) => s + v[j], 0) / n);
  const centered = vectors.map((v) => v.map((x, j) => x - mean[j]));

  // Mathematically correct power iteration to find top eigenvector of size D
  function powerIter(mat: number[][], iters = 25): number[] {
    const rows = mat.length;
    const cols = mat[0].length;
    let v = Array.from({ length: cols }, () => Math.random() - 0.5);
    
    for (let iter = 0; iter < iters; iter++) {
      // u = X v (size N)
      const u = mat.map((row) => row.reduce((s, val, j) => s + val * v[j], 0));
      
      // nextV = X^T u (size D)
      const nextV = Array.from({ length: cols }, () => 0.0);
      for (let i = 0; i < rows; i++) {
        for (let j = 0; j < cols; j++) {
          nextV[j] += mat[i][j] * u[i];
        }
      }
      
      const norm = Math.sqrt(nextV.reduce((s, x) => s + x * x, 0));
      v = nextV.map((x) => x / (norm || 1.0));
    }
    return v;
  }

  const pc1 = powerIter(centered);
  // Deflate
  const deflated = centered.map((row) => {
    const proj = row.reduce((s, val, j) => s + val * pc1[j], 0);
    return row.map((val, j) => val - proj * pc1[j]);
  });
  const pc2 = powerIter(deflated);

  return centered.map((row) => [
    row.reduce((s, val, j) => s + val * pc1[j], 0),
    row.reduce((s, val, j) => s + val * pc2[j], 0),
  ]);
}

const COLORS = ["#a78bfa","#34d399","#fb923c","#f472b6","#22d3ee","#fbbf24","#818cf8","#f43f5e","#4ade80","#60a5fa"];

export default function RepresentationsPage() {
  const [datasetsList, setDatasetsList] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [records, setRecords] = useState<EmbeddingRecord[]>([]);
  const [loading, setLoading] = useState(true);

  // Load datasets list first
  useEffect(() => {
    api.datasets()
      .then((list) => {
        setDatasetsList(list);
        if (list.length > 0) {
          setSelectedDatasetId(String(list[0].id));
        } else {
          api.registry({ limit: "1000" })
            .then(setRecords)
            .finally(() => setLoading(false));
        }
      })
      .catch(() => {
        api.registry({ limit: "1000" })
          .then(setRecords)
          .finally(() => setLoading(false));
      });
  }, []);

  // Fetch embeddings whenever selected dataset changes
  useEffect(() => {
    if (!selectedDatasetId) return;
    setLoading(true);
    api.registry({ dataset_id: selectedDatasetId, limit: "1500" })
      .then((res) => {
        setRecords(res);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [selectedDatasetId]);

  const { points, patientIds } = useMemo(() => {
    if (records.length < 2) return { points: [], patientIds: [] };
    const coords = pca2d(records.map((r) => r.vector));
    const ids = [...new Set(records.map((r) => r.patient_id))].sort((a, b) => a - b);
    const points = records.map((r, i) => ({
      x: coords[i] ? coords[i][0] : 0,
      y: coords[i] ? coords[i][1] : 0,
      patient_id: r.patient_id,
      created_at: r.created_at,
    }));
    return { points, patientIds: ids };
  }, [records]);

  return (
    <div className="max-w-4xl space-y-6 pb-16">
      <div>
        <h1 className="text-xl font-semibold text-zinc-100 font-sans tracking-tight">Representation Hub</h1>
        <p className="text-sm text-zinc-500 mt-1">
          PCA projection of 128-d HSF embeddings — each point maps one standardized daily UHS timeline representation
        </p>
      </div>

      {/* Dataset Selection Dropdown */}
      {datasetsList.length > 0 && (
        <div className="flex items-center gap-3 bg-zinc-900 border border-zinc-800 rounded-xl p-4 max-w-fit">
          <label className="text-xs text-zinc-400 font-semibold uppercase tracking-wider">Select Dataset Cohort</label>
          <select
            className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-1.5 text-xs text-zinc-200"
            value={selectedDatasetId}
            onChange={(e) => setSelectedDatasetId(e.target.value)}
          >
            {datasetsList.map((d) => (
              <option key={d.id} value={d.id}>{d.name} (v{d.version})</option>
            ))}
          </select>
        </div>
      )}

      <div className="flex items-center gap-4 text-xs text-zinc-500">
        <span>{records.length} embeddings</span>
        <span>{patientIds.length} cohort subjects</span>
        {loading && <span className="text-zinc-600 animate-pulse">Loading representations...</span>}
      </div>

      {points.length > 0 && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
          <ResponsiveContainer width="100%" height={420}>
            <ScatterChart>
              <XAxis dataKey="x" type="number" tick={{ fontSize: 9, fill: "#52525b" }} name="PC1" />
              <YAxis dataKey="y" type="number" tick={{ fontSize: 9, fill: "#52525b" }} name="PC2" />
              <Tooltip
                cursor={{ strokeDasharray: "3 3" }}
                contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", fontSize: 11 }}
                formatter={(v) => (typeof v === "number" ? v.toFixed(3) : String(v))}
                labelFormatter={() => ""}
              />
              {/* High-Performance Rendering: Single Scatter series colored by Cell */}
              <Scatter name="Subjects" data={points} opacity={0.75}>
                {points.map((p, idx) => (
                  <Cell
                    key={`cell-${idx}`}
                    fill={COLORS[patientIds.indexOf(p.patient_id) % COLORS.length]}
                  />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>

          {/* Clean Legend: Collapsed if there are more than 15 subjects */}
          <div className="flex flex-wrap gap-2 mt-4 max-h-24 overflow-y-auto border-t border-zinc-800/60 pt-3">
            {patientIds.slice(0, 15).map((pid, i) => (
              <span key={pid} className="flex items-center gap-1 text-[10px] text-zinc-400">
                <span className="w-2 h-2 rounded-full inline-block" style={{ background: COLORS[i % COLORS.length] }} />
                Subject #{pid}
              </span>
            ))}
            {patientIds.length > 15 && (
              <span className="text-[10px] text-zinc-500 font-medium">
                + {patientIds.length - 15} more subjects
              </span>
            )}
          </div>
        </div>
      )}

      {!loading && records.length === 0 && (
        <p className="text-sm text-zinc-600">No embeddings found. Ingest a dataset for this cohort first.</p>
      )}
    </div>
  );
}
