-- HormoneOS PostgreSQL Schema

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE patients (
    id          SERIAL PRIMARY KEY,
    uuid        UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    birth_year  INT,
    weight_kg   FLOAT,
    height_cm   FLOAT
);

CREATE TABLE datasets (
    id                     SERIAL PRIMARY KEY,
    name                   VARCHAR(255) NOT NULL UNIQUE,
    version                VARCHAR(50)  NOT NULL,
    sha256_hash            VARCHAR(64)  NOT NULL,
    transformation_history JSONB        NOT NULL DEFAULT '[]',
    created_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE cycles (
    id           SERIAL PRIMARY KEY,
    patient_id   INT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    cycle_number INT NOT NULL,
    phase        VARCHAR(20) NOT NULL CHECK (phase IN ('menstrual','follicular','ovulatory','luteal','unknown')),
    start_date   DATE,
    end_date     DATE
);

CREATE TABLE timeline (
    id           SERIAL PRIMARY KEY,
    patient_id   INT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    cycle_id     INT REFERENCES cycles(id),
    dataset_id   INT NOT NULL REFERENCES datasets(id),
    timestamp    TIMESTAMPTZ NOT NULL,
    day_in_study INT
);

CREATE TABLE wearables (
    id                   SERIAL PRIMARY KEY,
    timeline_id          INT NOT NULL REFERENCES timeline(id) ON DELETE CASCADE UNIQUE,
    heart_rate           FLOAT,
    active_minutes       FLOAT,
    computed_temperature FLOAT,
    vo2_max              FLOAT,
    vo2_max_error        FLOAT
);

CREATE TABLE hormones (
    id            SERIAL PRIMARY KEY,
    timeline_id   INT NOT NULL REFERENCES timeline(id) ON DELETE CASCADE UNIQUE,
    estrogen      FLOAT,
    progesterone  FLOAT,
    lh            FLOAT,
    fsh           FLOAT
);

CREATE TABLE symptoms (
    id           SERIAL PRIMARY KEY,
    timeline_id  INT NOT NULL REFERENCES timeline(id) ON DELETE CASCADE,
    symptom_name VARCHAR(100) NOT NULL,
    severity     INT NOT NULL CHECK (severity BETWEEN 1 AND 5)
);

CREATE TABLE glucose (
    id            SERIAL PRIMARY KEY,
    timeline_id   INT NOT NULL REFERENCES timeline(id) ON DELETE CASCADE UNIQUE,
    glucose_value FLOAT
);

CREATE TABLE embeddings (
    id            SERIAL PRIMARY KEY,
    timeline_id   INT NOT NULL REFERENCES timeline(id) ON DELETE CASCADE,
    model_version VARCHAR(50) NOT NULL,
    vector        FLOAT8[]    NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_timeline_patient  ON timeline(patient_id);
CREATE INDEX idx_timeline_cycle    ON timeline(cycle_id);
CREATE INDEX idx_timeline_dataset  ON timeline(dataset_id);
CREATE INDEX idx_timeline_ts       ON timeline(timestamp);
CREATE INDEX idx_embeddings_model  ON embeddings(model_version);
