#!/usr/bin/env python3
"""
Reusable Ingestion Utility for HormoneOS.
This script reads a JSON file of UHS-compliant records, registers the dataset,
and ingests the observations into the database.

Usage:
    python scripts/ingest_custom.py --file path/to/dataset.json --name "my-dataset" --version "1.0.0"
"""
import sys
import os
import argparse
import json
import hashlib
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))

from app.core.database import SessionLocal, engine, Base
from app.models import models as _models          # registers tables
from app.repositories.repos import DatasetRepo
from app.services.ingestion import ingest_records
from app.schemas.schemas import UHSRecord

# Initialize tables if not exist
Base.metadata.create_all(bind=engine)

def main():
    parser = argparse.ArgumentParser(description="Ingest a custom UHS JSON dataset into HormoneOS.")
    parser.add_argument("--file", required=True, help="Path to JSON file containing UHS records array")
    parser.add_argument("--name", required=True, help="Name of the dataset")
    parser.add_argument("--version", default="1.0.0", help="Dataset version tag")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File not found at {args.file}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading custom dataset from {args.file}...")
    with open(args.file, "r") as f:
        raw_data = json.load(f)

    # Compute SHA-256 hash of file for cryptographic tracking
    hasher = hashlib.sha256()
    with open(args.file, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    sha_hash = hasher.hexdigest()

    # Parse JSON records into Pydantic UHSRecords
    print("Validating records against Universal Hormonal Schema (UHS)...")
    records = []
    for idx, item in enumerate(raw_data):
        try:
            record = UHSRecord.model_validate(item)
            records.append(record)
        except Exception as e:
            print(f"Validation error at index {idx}: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"Successfully validated {len(records)} UHS records.")

    db = SessionLocal()
    try:
        repo = DatasetRepo(db)
        dataset = repo.get_by_name(args.name)
        if not dataset:
            print(f"Registering dataset '{args.name}' v{args.version} in Dataset Registry...")
            dataset = repo.create(
                name=args.name,
                version=args.version,
                sha256_hash=sha_hash,
                transformation_history=[{
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "operator": "ingest_custom.py",
                    "action": f"Ingested {len(records)} custom records from JSON"
                }]
            )
            db.commit()
            print(f"Dataset registered. ID: {dataset.id}")
        else:
            print(f"Dataset '{args.name}' already registered (ID: {dataset.id}). Appending records...")

        print("Ingesting records and generating HSF representation vectors...")
        result = ingest_records(db, dataset.id, records)
        print(f"✓ Ingestion Complete: inserted={result.inserted}  skipped={result.skipped}  errors={len(result.errors)}")
        if result.errors:
            print("Errors encountered during ingestion:")
            for err in result.errors[:10]:
                print(f"  - {err}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
