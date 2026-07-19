from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime,
    ForeignKey, JSON, CheckConstraint, UniqueConstraint, ARRAY
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Patient(Base):
    __tablename__ = "patients"
    id         = Column(Integer, primary_key=True)
    uuid       = Column(String(36), unique=True, nullable=False)
    birth_year = Column(Integer)
    weight_kg  = Column(Float)
    height_cm  = Column(Float)

    cycles   = relationship("Cycle",    back_populates="patient", cascade="all, delete")
    timeline = relationship("Timeline", back_populates="patient", cascade="all, delete")


class Dataset(Base):
    __tablename__ = "datasets"
    id                     = Column(Integer, primary_key=True)
    name                   = Column(String(255), unique=True, nullable=False)
    version                = Column(String(50), nullable=False)
    sha256_hash            = Column(String(64), nullable=False)
    transformation_history = Column(JSON, default=list)
    created_at             = Column(DateTime, default=datetime.utcnow)

    timeline = relationship("Timeline", back_populates="dataset")


class Cycle(Base):
    __tablename__ = "cycles"
    __table_args__ = (
        CheckConstraint("phase IN ('menstrual','follicular','ovulatory','luteal','unknown')", name="ck_cycle_phase"),
    )
    id           = Column(Integer, primary_key=True)
    patient_id   = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    cycle_number = Column(Integer, nullable=False)
    phase        = Column(String(20), nullable=False)
    start_date   = Column(Date)
    end_date     = Column(Date)

    patient  = relationship("Patient",  back_populates="cycles")
    timeline = relationship("Timeline", back_populates="cycle")


class Timeline(Base):
    __tablename__ = "timeline"
    id           = Column(Integer, primary_key=True)
    patient_id   = Column(Integer, ForeignKey("patients.id",  ondelete="CASCADE"), nullable=False)
    cycle_id     = Column(Integer, ForeignKey("cycles.id"))
    dataset_id   = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    timestamp    = Column(DateTime, nullable=False)
    day_in_study = Column(Integer)

    patient    = relationship("Patient",  back_populates="timeline")
    cycle      = relationship("Cycle",    back_populates="timeline")
    dataset    = relationship("Dataset",  back_populates="timeline")
    wearable   = relationship("Wearable", back_populates="timeline", uselist=False, cascade="all, delete")
    hormone    = relationship("Hormone",  back_populates="timeline", uselist=False, cascade="all, delete")
    symptoms   = relationship("Symptom",  back_populates="timeline", cascade="all, delete")
    glucose    = relationship("Glucose",  back_populates="timeline", uselist=False, cascade="all, delete")
    embeddings = relationship("Embedding", back_populates="timeline", cascade="all, delete")


class Wearable(Base):
    __tablename__ = "wearables"
    id                   = Column(Integer, primary_key=True)
    timeline_id          = Column(Integer, ForeignKey("timeline.id", ondelete="CASCADE"), unique=True, nullable=False)
    heart_rate           = Column(Float)
    active_minutes       = Column(Float)
    computed_temperature = Column(Float)
    vo2_max              = Column(Float)
    vo2_max_error        = Column(Float)

    timeline = relationship("Timeline", back_populates="wearable")


class Hormone(Base):
    __tablename__ = "hormones"
    id           = Column(Integer, primary_key=True)
    timeline_id  = Column(Integer, ForeignKey("timeline.id", ondelete="CASCADE"), unique=True, nullable=False)
    estrogen     = Column(Float)
    progesterone = Column(Float)
    lh           = Column(Float)
    fsh          = Column(Float)

    timeline = relationship("Timeline", back_populates="hormone")


class Symptom(Base):
    __tablename__ = "symptoms"
    __table_args__ = (
        CheckConstraint("severity BETWEEN 1 AND 5", name="ck_symptom_severity"),
    )
    id           = Column(Integer, primary_key=True)
    timeline_id  = Column(Integer, ForeignKey("timeline.id", ondelete="CASCADE"), nullable=False)
    symptom_name = Column(String(100), nullable=False)
    severity     = Column(Integer, nullable=False)

    timeline = relationship("Timeline", back_populates="symptoms")


class Glucose(Base):
    __tablename__ = "glucose"
    id            = Column(Integer, primary_key=True)
    timeline_id   = Column(Integer, ForeignKey("timeline.id", ondelete="CASCADE"), unique=True, nullable=False)
    glucose_value = Column(Float)

    timeline = relationship("Timeline", back_populates="glucose")


class Embedding(Base):
    __tablename__ = "embeddings"
    id            = Column(Integer, primary_key=True)
    timeline_id   = Column(Integer, ForeignKey("timeline.id", ondelete="CASCADE"), nullable=False)
    model_version = Column(String(50), nullable=False)
    vector        = Column(ARRAY(Float), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    timeline = relationship("Timeline", back_populates="embeddings")
