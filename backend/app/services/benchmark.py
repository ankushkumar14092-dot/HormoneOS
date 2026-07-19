import numpy as np
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import Timeline, Cycle, Embedding
from app.schemas.schemas import BenchmarkOut

PHASE_MAP = {"menstrual": 0, "follicular": 1, "ovulatory": 2, "luteal": 3, "unknown": 4}


def run_benchmark(db: Session, task: str, patient_ids: Optional[List[int]] = None) -> BenchmarkOut:
    q = db.query(Embedding).join(Timeline, Embedding.timeline_id == Timeline.id)
    if patient_ids:
        q = q.filter(Timeline.patient_id.in_(patient_ids))
    embeddings = q.all()

    if not embeddings:
        return BenchmarkOut(task=task, details={"error": "No embeddings found"})

    vectors = np.array([e.vector for e in embeddings], dtype=np.float32)

    if task == "phase_classification":
        labels = []
        for e in embeddings:
            tl = db.query(Timeline).filter(Timeline.id == e.timeline_id).first()
            cycle = db.query(Cycle).filter(Cycle.id == tl.cycle_id).first() if tl and tl.cycle_id else None
            labels.append(PHASE_MAP.get(cycle.phase if cycle else "unknown", 4))

        labels = np.array(labels)
        # Nearest-centroid leave-one-out accuracy (lightweight, no sklearn dependency)
        correct = 0
        for i in range(len(vectors)):
            mask = np.ones(len(vectors), dtype=bool)
            mask[i] = False
            train_v, train_l = vectors[mask], labels[mask]
            centroids = {c: train_v[train_l == c].mean(axis=0) for c in np.unique(train_l)}
            pred = min(centroids, key=lambda c: np.linalg.norm(vectors[i] - centroids[c]))
            correct += int(pred == labels[i])

        acc = round(correct / len(vectors), 4)
        return BenchmarkOut(task=task, accuracy=acc, details={"n_samples": len(vectors)})

    elif task == "hormone_regression":
        # Predict estrogen from embedding via ridge-like closed-form
        from app.models.models import Hormone
        targets = []
        for e in embeddings:
            h = db.query(Hormone).filter(Hormone.timeline_id == e.timeline_id).first()
            targets.append(h.estrogen if h and h.estrogen is not None else 0.0)

        y = np.array(targets, dtype=np.float32)
        X = np.hstack([vectors, np.ones((len(vectors), 1))])
        # Ridge regression: w = (X'X + λI)^-1 X'y
        lam = 1e-3
        w = np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]), X.T @ y)
        preds = X @ w
        rmse  = float(np.sqrt(np.mean((preds - y) ** 2)))
        return BenchmarkOut(task=task, rmse=round(rmse, 4), details={"n_samples": len(vectors)})

    return BenchmarkOut(task=task, details={"error": f"Unknown task: {task}"})
