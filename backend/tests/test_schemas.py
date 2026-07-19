"""Validation tests for the Universal Hormonal Schema (UHS)."""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.schemas import (
    CycleInfo,
    SymptomEntry,
    UHSRecord,
    WearableData,
)


def test_uhs_record_minimal():
    rec = UHSRecord(patient_id=1, timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc))
    assert rec.patient_id == 1
    assert rec.symptoms == []
    assert rec.wearables is None


def test_uhs_record_full_roundtrip():
    rec = UHSRecord(
        patient_id=2,
        timestamp=datetime(2024, 1, 2, tzinfo=timezone.utc),
        day_in_study=3,
        cycle=CycleInfo(cycle_number=1, phase="ovulatory"),
        wearables=WearableData(heart_rate_bpm=65.0, active_minutes=40.0),
        symptoms=[SymptomEntry(name="cramps", severity=3)],
    )
    dumped = rec.model_dump()
    restored = UHSRecord(**dumped)
    assert restored.cycle.phase == "ovulatory"
    assert restored.wearables.heart_rate_bpm == 65.0
    assert restored.symptoms[0].severity == 3


@pytest.mark.parametrize("severity", [0, 6, -1, 100])
def test_symptom_severity_out_of_range_rejected(severity):
    with pytest.raises(ValidationError):
        SymptomEntry(name="headache", severity=severity)


@pytest.mark.parametrize("severity", [1, 3, 5])
def test_symptom_severity_in_range_accepted(severity):
    assert SymptomEntry(name="headache", severity=severity).severity == severity


def test_invalid_phase_rejected():
    with pytest.raises(ValidationError):
        CycleInfo(cycle_number=1, phase="not_a_phase")
