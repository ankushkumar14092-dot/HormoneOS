import os
import sys
import logging
import numpy as np
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.schemas.schemas import UHSRecord, RepresentationOut, ExplainOut
from app.repositories.repos import EmbeddingRepo, TimelineRepo
from app.core.config import settings
from app.services.llm_service import explain_narrative

logger = logging.getLogger(__name__)

# Cache the loaded encoder so we don't rebuild (and re-load weights) on every
# request. `False` is a sentinel meaning "we tried and torch/the model is
# unavailable", so we skip retrying on every call.
_ENCODER_CACHE: object = None


def _load_encoder():
    """Build the HSF encoder once, loading trained weights if available.

    Returns the eval-mode encoder, or None if torch / the ml module is not
    available (callers then fall back to a deterministic random projection).
    """
    global _ENCODER_CACHE
    if _ENCODER_CACHE is not None:
        return _ENCODER_CACHE or None  # unwrap the False sentinel

    try:
        if settings.ML_SRC_DIR not in sys.path:
            sys.path.insert(0, settings.ML_SRC_DIR)
        import torch
        from models import HSFEncoder

        model = HSFEncoder(input_dim=9, hidden_dim=256, embed_dim=settings.EMBEDDING_DIM)
        if os.path.exists(settings.HSF_WEIGHTS_PATH):
            state = torch.load(settings.HSF_WEIGHTS_PATH, map_location="cpu")
            model.load_state_dict(state)
            logger.info("Loaded HSF weights from %s", settings.HSF_WEIGHTS_PATH)
        else:
            logger.warning(
                "HSF weights not found at %s; using an untrained encoder. "
                "Run `python ml/src/train.py` to produce a checkpoint.",
                settings.HSF_WEIGHTS_PATH,
            )
        model.eval()
        _ENCODER_CACHE = model
        return model
    except Exception as exc:  # torch missing, import error, bad checkpoint, etc.
        logger.warning("HSF encoder unavailable (%s); using fallback projection", exc)
        _ENCODER_CACHE = False
        return None


FEATURE_NAMES = [
    "heart_rate", "active_minutes", "computed_temperature",
    "vo2_max", "estrogen", "progesterone", "lh", "fsh", "glucose",
]


def _records_to_matrix(records: List[UHSRecord]) -> np.ndarray:
    rows = []
    for r in records:
        w = r.wearables or {}
        h = r.hormones  or {}
        g = r.glucose   or {}
        row = [
            getattr(w, "heart_rate_bpm",         None) or 0.0,
            getattr(w, "active_minutes",          None) or 0.0,
            getattr(w, "computed_temperature_c",  None) or 0.0,
            getattr(w, "vo2_max",                 None) or 0.0,
            getattr(h, "estrogen_pg_ml",          None) or 0.0,
            getattr(h, "progesterone_ng_ml",      None) or 0.0,
            getattr(h, "lh_miu_ml",               None) or 0.0,
            getattr(h, "fsh_miu_ml",              None) or 0.0,
            getattr(g, "glucose_mg_dl",           None) or 0.0,
        ]
        rows.append(row)
    return np.array(rows, dtype=np.float32)


def _fallback_vector(matrix: np.ndarray) -> List[float]:
    """Deterministic mean-pool + fixed random projection to EMBEDDING_DIM."""
    rng = np.random.default_rng(42)
    proj = rng.standard_normal((matrix.shape[1], settings.EMBEDDING_DIM)).astype(np.float32)
    mean = matrix.mean(axis=0)
    raw = mean @ proj
    norm = np.linalg.norm(raw)
    return (raw / norm if norm > 0 else raw).tolist()


def encode_records(records: List[UHSRecord]) -> List[float]:
    """Turn a sequence of UHS records into a single normalized embedding.

    Pure (no DB side effects): uses the cached HSF encoder when available and
    otherwise a deterministic projection so results are reproducible.
    """
    matrix = _records_to_matrix(records)  # (T, 9)
    if matrix.size == 0:
        return [0.0] * settings.EMBEDDING_DIM

    model = _load_encoder()
    if model is not None:
        try:
            import torch
            with torch.no_grad():
                x = torch.tensor(matrix).unsqueeze(0)  # (1, T, 9)
                vector, _ = model(x)
                return vector.squeeze(0).numpy().tolist()
        except Exception as exc:
            logger.warning("HSF inference failed (%s); using fallback projection", exc)

    return _fallback_vector(matrix)


def generate_representation(db: Session, patient_id: int, records: List[UHSRecord]) -> RepresentationOut:
    vector = encode_records(records)

    # Persist one embedding per timeline row
    emb_repo = EmbeddingRepo(db)
    tl_rows  = TimelineRepo(db).get_by_patient(patient_id)
    if tl_rows:
        emb_repo.create(tl_rows[-1].id, settings.HSF_MODEL_VERSION, vector)
        db.commit()

    return RepresentationOut(
        patient_id=patient_id,
        model_version=settings.HSF_MODEL_VERSION,
        vector=vector,
        dim=len(vector),
    )


def explain_representation(patient_id: int, records: List[UHSRecord]) -> ExplainOut:
    matrix = _records_to_matrix(records)
    norms   = np.linalg.norm(matrix, axis=1)
    exp     = np.exp(norms - norms.max())
    weights = (exp / exp.sum()).tolist()
    narrative = explain_narrative(patient_id, weights, FEATURE_NAMES)
    return ExplainOut(
        patient_id=patient_id,
        attention_weights=weights,
        feature_names=FEATURE_NAMES,
        narrative=narrative,
    )
