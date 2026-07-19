from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import Patient, Dataset, Cycle, Timeline, Wearable, Hormone, Symptom, Glucose, Embedding


class PatientRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, uuid: str, birth_year=None, weight_kg=None, height_cm=None) -> Patient:
        p = Patient(uuid=uuid, birth_year=birth_year, weight_kg=weight_kg, height_cm=height_cm)
        self.db.add(p)
        self.db.flush()
        return p

    def create_with_id(self, patient_id: int, uuid: str, birth_year=None, weight_kg=None, height_cm=None) -> Patient:
        p = Patient(id=patient_id, uuid=uuid, birth_year=birth_year, weight_kg=weight_kg, height_cm=height_cm)
        self.db.add(p)
        self.db.flush()
        return p

    def get(self, patient_id: int) -> Optional[Patient]:
        return self.db.query(Patient).filter(Patient.id == patient_id).first()

    def list_all(self) -> List[Patient]:
        return self.db.query(Patient).all()


class DatasetRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name, version, sha256_hash, transformation_history=None) -> Dataset:
        d = Dataset(name=name, version=version, sha256_hash=sha256_hash,
                    transformation_history=transformation_history or [])
        self.db.add(d)
        self.db.flush()
        return d

    def get(self, dataset_id: int) -> Optional[Dataset]:
        return self.db.query(Dataset).filter(Dataset.id == dataset_id).first()

    def get_by_name(self, name: str) -> Optional[Dataset]:
        return self.db.query(Dataset).filter(Dataset.name == name).first()

    def list_all(self) -> List[Dataset]:
        return self.db.query(Dataset).all()


class TimelineRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, patient_id, dataset_id, timestamp, day_in_study=None, cycle_id=None) -> Timeline:
        t = Timeline(patient_id=patient_id, dataset_id=dataset_id,
                     timestamp=timestamp, day_in_study=day_in_study, cycle_id=cycle_id)
        self.db.add(t)
        self.db.flush()
        return t

    def get_by_patient(self, patient_id: int, start=None, end=None) -> List[Timeline]:
        q = self.db.query(Timeline).filter(Timeline.patient_id == patient_id)
        if start:
            q = q.filter(Timeline.timestamp >= start)
        if end:
            q = q.filter(Timeline.timestamp <= end)
        return q.order_by(Timeline.timestamp).all()


class CycleRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, patient_id, cycle_number, phase, start_date=None) -> Cycle:
        c = self.db.query(Cycle).filter(
            Cycle.patient_id == patient_id,
            Cycle.cycle_number == cycle_number
        ).first()
        if not c:
            c = Cycle(patient_id=patient_id, cycle_number=cycle_number,
                      phase=phase, start_date=start_date)
            self.db.add(c)
            self.db.flush()
        return c


class EmbeddingRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, timeline_id, model_version, vector) -> Embedding:
        e = Embedding(timeline_id=timeline_id, model_version=model_version, vector=vector)
        self.db.add(e)
        self.db.flush()
        return e

    def get_by_patient(self, patient_id: int, model_version: Optional[str] = None) -> List[Embedding]:
        q = (self.db.query(Embedding)
             .join(Timeline, Embedding.timeline_id == Timeline.id)
             .filter(Timeline.patient_id == patient_id))
        if model_version:
            q = q.filter(Embedding.model_version == model_version)
        return q.order_by(Timeline.timestamp).all()

    def search(self, patient_id=None, model_version=None, dataset_id=None, limit=50) -> List[Embedding]:
        q = self.db.query(Embedding).join(Timeline, Embedding.timeline_id == Timeline.id)
        if patient_id:
            q = q.filter(Timeline.patient_id == patient_id)
        if model_version:
            q = q.filter(Embedding.model_version == model_version)
        if dataset_id:
            q = q.filter(Timeline.dataset_id == dataset_id)
        return q.limit(limit).all()
