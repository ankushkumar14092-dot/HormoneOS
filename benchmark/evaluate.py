#!/usr/bin/env python3
"""
Run downstream benchmark tasks against stored HSF embeddings.

Usage:
    python evaluate.py --task phase_classification
    python evaluate.py --task hormone_regression
"""
import sys, os, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))

import numpy as np
from app.core.database import SessionLocal
from app.services.benchmark import run_benchmark


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=["phase_classification", "hormone_regression"],
                        default="phase_classification")
    parser.add_argument("--patient-ids", nargs="*", type=int, default=None)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = run_benchmark(db, args.task, args.patient_ids)
        print(f"\n── Benchmark: {result.task} ──")
        if result.accuracy is not None:
            print(f"  Accuracy : {result.accuracy:.4f}")
        if result.f1 is not None:
            print(f"  F1       : {result.f1:.4f}")
        if result.rmse is not None:
            print(f"  RMSE     : {result.rmse:.4f}")
        print(f"  Details  : {result.details}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
