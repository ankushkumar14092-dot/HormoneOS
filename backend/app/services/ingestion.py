import hashlib, uuid
from typing import List
from sqlalchemy.orm import Session
from app.models.models import Wearable, Hormone, Symptom, Glucose
from app.repositories.repos import PatientRepo, DatasetRepo, TimelineRepo, CycleRepo
from app.schemas.schemas import UHSRecord, IngestResponse
from app.services.llm_service import ingestion_summary


def ingest_records(db: Session, dataset_id: int, records: List[UHSRecord]) -> IngestResponse:
    dataset_repo  = DatasetRepo(db)
    patient_repo  = PatientRepo(db)
    timeline_repo = TimelineRepo(db)
    cycle_repo    = CycleRepo(db)

    if not dataset_repo.get(dataset_id):
        return IngestResponse(inserted=0, skipped=0, errors=[f"Dataset {dataset_id} not found"])

    inserted, skipped, errors = 0, 0, []

    for rec in records:
        try:
            patient = patient_repo.get(rec.patient_id)
            if not patient:
                patient = patient_repo.create_with_id(
                    rec.patient_id,
                    uuid=str(uuid.uuid4()),
                    birth_year=getattr(rec, "birth_year", None),
                    weight_kg=getattr(rec, "weight_kg", None),
                    height_cm=getattr(rec, "height_cm", None)
                )

            cycle_id = None
            if rec.cycle:
                cycle = cycle_repo.get_or_create(
                    patient_id=patient.id,
                    cycle_number=rec.cycle.cycle_number,
                    phase=rec.cycle.phase,
                )
                cycle_id = cycle.id

            tl = timeline_repo.create(
                patient_id=patient.id,
                dataset_id=dataset_id,
                timestamp=rec.timestamp,
                day_in_study=rec.day_in_study,
                cycle_id=cycle_id,
            )

            if rec.wearables:
                w = rec.wearables
                db.add(Wearable(
                    timeline_id=tl.id,
                    heart_rate=w.heart_rate_bpm,
                    active_minutes=w.active_minutes,
                    computed_temperature=w.computed_temperature_c,
                    vo2_max=w.vo2_max,
                    vo2_max_error=w.vo2_max_error,
                ))

            if rec.hormones:
                h = rec.hormones
                db.add(Hormone(
                    timeline_id=tl.id,
                    estrogen=h.estrogen_pg_ml,
                    progesterone=h.progesterone_ng_ml,
                    lh=h.lh_miu_ml,
                    fsh=h.fsh_miu_ml,
                ))

            for s in rec.symptoms:
                db.add(Symptom(timeline_id=tl.id, symptom_name=s.name, severity=s.severity))

            if rec.glucose:
                db.add(Glucose(timeline_id=tl.id, glucose_value=rec.glucose.glucose_mg_dl))

            inserted += 1

        except Exception as e:
            errors.append(f"Record patient={rec.patient_id} ts={rec.timestamp}: {e}")
            skipped += 1

    db.commit()

    # Auto-generate transformation action via LLM and append to dataset history
    action = ingestion_summary(
        dataset_name=dataset_repo.get(dataset_id).name,
        n_records=inserted,
        n_patients=len({r.patient_id for r in records}),
        n_errors=skipped,
        columns_joined=["heart_rate", "active_minutes", "computed_temperature",
                        "vo2_max", "hormones", "glucose", "symptoms"],
    )
    dataset = dataset_repo.get(dataset_id)
    history = list(dataset.transformation_history or [])
    import datetime
    history.append({
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "operator":  "IngestionService",
        "action":    action,
    })
    dataset.transformation_history = history
    db.commit()

    return IngestResponse(inserted=inserted, skipped=skipped, errors=errors,
                          transformation_action=action)
