"""Tests for the HSF representation service (DB-free)."""
from datetime import datetime, timezone

import numpy as np

from app.core.config import settings
from app.schemas.schemas import GlucoseData, HormoneData, UHSRecord, WearableData
from app.services import hsf_service


def _record(hr=60.0, est=100.0, glu=90.0):
    return UHSRecord(
        patient_id=1,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        wearables=WearableData(heart_rate_bpm=hr, active_minutes=30.0),
        hormones=HormoneData(estrogen_pg_ml=est),
        glucose=GlucoseData(glucose_mg_dl=glu),
    )


def test_records_to_matrix_shape_and_values():
    records = [_record(hr=60), _record(hr=70), _record(hr=80)]
    matrix = hsf_service._records_to_matrix(records)
    assert matrix.shape == (3, 9)
    assert matrix.dtype == np.float32
    # heart_rate is the first feature column
    assert list(matrix[:, 0]) == [60.0, 70.0, 80.0]


def test_encode_records_returns_normalized_vector():
    vector = hsf_service.encode_records([_record(), _record(hr=72)])
    assert len(vector) == settings.EMBEDDING_DIM
    assert all(np.isfinite(vector))
    # Both the HSF encoder and the fallback L2-normalize their output.
    assert np.isclose(np.linalg.norm(vector), 1.0, atol=1e-4)


def test_encode_empty_records_returns_zero_vector():
    assert hsf_service.encode_records([]) == [0.0] * settings.EMBEDDING_DIM


def test_fallback_projection_is_deterministic():
    matrix = np.random.default_rng(0).standard_normal((5, 9)).astype(np.float32)
    v1 = hsf_service._fallback_vector(matrix)
    v2 = hsf_service._fallback_vector(matrix)
    assert v1 == v2
    assert len(v1) == settings.EMBEDDING_DIM
    assert np.isclose(np.linalg.norm(v1), 1.0, atol=1e-5)


def test_encode_uses_fallback_when_encoder_unavailable(monkeypatch):
    monkeypatch.setattr(hsf_service, "_load_encoder", lambda: None)
    records = [_record(), _record(hr=90)]
    vector = hsf_service.encode_records(records)
    expected = hsf_service._fallback_vector(hsf_service._records_to_matrix(records))
    assert vector == expected
