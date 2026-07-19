from __future__ import annotations
from datetime import datetime, date
from typing import List, Optional, Literal, Any
from pydantic import BaseModel, Field, field_validator


# ── Dataset / Versioning ──────────────────────────────────────────────────────

class TransformationEntry(BaseModel):
    timestamp: datetime
    operator: str
    action: str


class DatasetCreate(BaseModel):
    name: str
    version: str
    sha256_hash: str
    transformation_history: List[TransformationEntry] = []


class DatasetOut(DatasetCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── UHS sub-objects ───────────────────────────────────────────────────────────

class CycleInfo(BaseModel):
    cycle_number: int
    phase: Literal["menstrual", "follicular", "ovulatory", "luteal", "unknown"]


class WearableData(BaseModel):
    heart_rate_bpm:          Optional[float] = None
    active_minutes:          Optional[float] = None
    computed_temperature_c:  Optional[float] = None
    vo2_max:                 Optional[float] = None
    vo2_max_error:           Optional[float] = None


class HormoneData(BaseModel):
    estrogen_pg_ml:      Optional[float] = None
    progesterone_ng_ml:  Optional[float] = None
    lh_miu_ml:           Optional[float] = None
    fsh_miu_ml:          Optional[float] = None


class SymptomEntry(BaseModel):
    name:     str
    severity: int = Field(..., ge=1, le=5)


class GlucoseData(BaseModel):
    glucose_mg_dl: Optional[float] = None


# ── Universal Hormonal Schema (UHS) ──────────────────────────────────────────

class UHSRecord(BaseModel):
    patient_id:   int
    timestamp:    datetime
    day_in_study: Optional[int] = None
    cycle:        Optional[CycleInfo]   = None
    wearables:    Optional[WearableData] = None
    hormones:     Optional[HormoneData]  = None
    symptoms:     List[SymptomEntry]     = []
    glucose:      Optional[GlucoseData]  = None
    birth_year:   Optional[int] = None
    weight_kg:    Optional[float] = None
    height_cm:    Optional[float] = None


class IngestRequest(BaseModel):
    dataset_id:    int
    records:       List[UHSRecord]


class IngestResponse(BaseModel):
    inserted:              int
    skipped:               int
    errors:                List[str] = []
    transformation_action: Optional[str] = None


# ── Patient ───────────────────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    birth_year: Optional[int]   = None
    weight_kg:  Optional[float] = None
    height_cm:  Optional[float] = None


class PatientOut(PatientCreate):
    id:   int
    uuid: str

    class Config:
        from_attributes = True


# ── Timeline ──────────────────────────────────────────────────────────────────

class TimelineOut(BaseModel):
    id:           int
    patient_id:   int
    cycle_id:     Optional[int]
    dataset_id:   int
    timestamp:    datetime
    day_in_study: Optional[int]
    wearables:    Optional[WearableData]
    hormones:     Optional[HormoneData]
    symptoms:     List[SymptomEntry]
    glucose:      Optional[GlucoseData]

    class Config:
        from_attributes = True


# ── Embeddings / Representation ───────────────────────────────────────────────

class RepresentationRequest(BaseModel):
    patient_id: int
    records:    List[UHSRecord]


class RepresentationOut(BaseModel):
    patient_id:    int
    model_version: str
    vector:        List[float]
    dim:           int


# ── Comparison ────────────────────────────────────────────────────────────────

class CompareRequest(BaseModel):
    patient_a_id: int
    patient_b_id: int


class CompareOut(BaseModel):
    patient_a_id:     int
    patient_b_id:     int
    cosine_similarity: float
    dtw_distance:      float
    similarity_score:  float = Field(..., ge=0.0, le=1.0)
    narrative:         Optional[str] = None


# ── Registry search ───────────────────────────────────────────────────────────

class RegistrySearchParams(BaseModel):
    patient_id:    Optional[int]   = None
    model_version: Optional[str]   = None
    limit:         int             = 50


class EmbeddingOut(BaseModel):
    id:            int
    timeline_id:   int
    patient_id:    int
    model_version: str
    vector:        List[float]
    created_at:    datetime

    class Config:
        from_attributes = True


# ── Benchmark ─────────────────────────────────────────────────────────────────

class BenchmarkRequest(BaseModel):
    task:       Literal["phase_classification", "hormone_regression"]
    patient_ids: Optional[List[int]] = None


class BenchmarkOut(BaseModel):
    task:     str
    accuracy: Optional[float] = None
    f1:       Optional[float] = None
    rmse:     Optional[float] = None
    details:  dict            = {}


# ── Explain ───────────────────────────────────────────────────────────────────

class ExplainRequest(BaseModel):
    patient_id: int
    records:    List[UHSRecord]


class ExplainOut(BaseModel):
    patient_id:        int
    attention_weights: List[float]
    feature_names:     List[str]
    narrative:         Optional[str] = None
