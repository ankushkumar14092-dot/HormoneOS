const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`);
  return res.json();
}

export const api = {
  health:    ()                               => get("/api/v1/health"),
  patients:  ()                               => get<import("@/types").Patient[]>("/api/v1/patients"),
  patient:   (id: number)                     => get<import("@/types").Patient>(`/api/v1/patients/${id}`),
  timeline:  (id: number)                     => get<import("@/types").TimelineRow[]>(`/api/v1/timeline/${id}`),
  registry:  (params?: Record<string,string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return get<import("@/types").EmbeddingRecord[]>(`/api/v1/registry/search${qs}`);
  },
  compare:   (a: number, b: number)           => post<import("@/types").CompareResult>("/api/v1/representation/compare", { patient_a_id: a, patient_b_id: b }),
  benchmark: (task: string)                   => post<import("@/types").BenchmarkResult>("/api/v1/benchmark", { task }),
  datasets:  ()                               => get<any[]>("/api/v1/datasets"),
  datasetVersions: (name: string)             => get<any>(`/api/v1/datasets/versions?name=${encodeURIComponent(name)}`),
};
