export interface Patient {
  id: number;
  uuid: string;
  birth_year: number | null;
  weight_kg: number | null;
  height_cm: number | null;
}

export interface Dataset {
  id: number;
  name: string;
  version: string;
  sha256_hash: string;
  transformation_history: TransformationEntry[];
  created_at: string;
}

export interface TransformationEntry {
  timestamp: string;
  operator: string;
  action: string;
}

export interface WearableData {
  heart_rate_bpm: number | null;
  active_minutes: number | null;
  computed_temperature_c: number | null;
  vo2_max: number | null;
  vo2_max_error: number | null;
}

export interface HormoneData {
  estrogen_pg_ml: number | null;
  progesterone_ng_ml: number | null;
  lh_miu_ml: number | null;
  fsh_miu_ml: number | null;
}

export interface SymptomEntry {
  name: string;
  severity: number;
}

export interface TimelineRow {
  id: number;
  patient_id: number;
  cycle_id: number | null;
  dataset_id: number;
  timestamp: string;
  day_in_study: number | null;
  wearables: WearableData | null;
  hormones: HormoneData | null;
  symptoms: SymptomEntry[];
  glucose: { glucose_mg_dl: number | null } | null;
}

export interface EmbeddingRecord {
  id: number;
  timeline_id: number;
  patient_id: number;
  model_version: string;
  vector: number[];
  created_at: string;
}

export interface CompareResult {
  patient_a_id: number;
  patient_b_id: number;
  cosine_similarity: number;
  dtw_distance: number;
  similarity_score: number;
  narrative?: string | null;
}

export interface BenchmarkResult {
  task: string;
  accuracy: number | null;
  f1: number | null;
  rmse: number | null;
  details: Record<string, unknown>;
}
