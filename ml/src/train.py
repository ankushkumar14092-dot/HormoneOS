import argparse
import os

import torch
import torch.nn as nn
import torch.nn.functional as F
import yaml
from torch.utils.data import DataLoader

from dataset import FEATURE_COLS, PHASE_MAP, HormonalSequenceDataset, collate_fn
from models import HSFEncoder

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(HERE, "..", "config.yaml")
WEIGHTS_DIR = os.path.join(HERE, "weights")


def load_config(path: str = DEFAULT_CONFIG) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def contrastive_loss(emb: torch.Tensor, labels: torch.Tensor, margin: float = 0.5) -> torch.Tensor:
    """Supervised contrastive loss (simplified pairwise)."""
    B = emb.size(0)
    sim = F.cosine_similarity(emb.unsqueeze(1), emb.unsqueeze(0), dim=-1)  # (B, B)
    same = (labels.unsqueeze(1) == labels.unsqueeze(0)).float()
    pos  = same * (1 - sim)
    neg  = (1 - same) * F.relu(sim - margin)
    mask = 1 - torch.eye(B, device=emb.device)
    loss = ((pos + neg) * mask).sum() / (mask.sum() + 1e-8)
    return loss


def load_db_samples(input_dim: int, max_patients: int = 0) -> list:
    """Build training samples from the backend database.

    Each sample is one patient's ordered timeline as a (T, input_dim) feature
    matrix, labelled with that patient's dominant cycle phase. Related tables
    are bulk-loaded into dicts to avoid per-row (N+1) queries.

    Set ``max_patients`` > 0 to train on a random subset for a quick checkpoint.
    """
    import sys
    from collections import Counter

    import numpy as np

    backend = os.path.join(HERE, "..", "..", "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)

    from app.core.database import SessionLocal
    from app.models.models import Timeline, Wearable, Hormone, Glucose, Cycle

    db = SessionLocal()
    try:
        # Bulk-load related tables once, keyed for O(1) lookup.
        wearables = {w.timeline_id: w for w in db.query(Wearable).all()}
        hormones  = {h.timeline_id: h for h in db.query(Hormone).all()}
        glucose   = {g.timeline_id: g for g in db.query(Glucose).all()}
        cycles    = {c.id: c for c in db.query(Cycle).all()}

        rows = db.query(Timeline).order_by(Timeline.patient_id, Timeline.timestamp).all()

        by_patient: dict[int, list] = {}
        for tl in rows:
            by_patient.setdefault(tl.patient_id, []).append(tl)

        patient_ids = list(by_patient.keys())
        if max_patients and len(patient_ids) > max_patients:
            rng = np.random.default_rng(42)
            patient_ids = list(rng.choice(patient_ids, size=max_patients, replace=False))

        samples = []
        for pid in patient_ids:
            features, phases = [], []
            for tl in by_patient[pid]:
                w = wearables.get(tl.id)
                h = hormones.get(tl.id)
                g = glucose.get(tl.id)
                features.append([
                    (w.heart_rate if w else None) or 0.0,
                    (w.active_minutes if w else None) or 0.0,
                    (w.computed_temperature if w else None) or 0.0,
                    (w.vo2_max if w else None) or 0.0,
                    (h.estrogen if h else None) or 0.0,
                    (h.progesterone if h else None) or 0.0,
                    (h.lh if h else None) or 0.0,
                    (h.fsh if h else None) or 0.0,
                    (g.glucose_value if g else None) or 0.0,
                ])
                cycle = cycles.get(tl.cycle_id) if tl.cycle_id else None
                phases.append(PHASE_MAP.get(cycle.phase if cycle else "unknown", 4))

            arr = np.asarray(features, dtype="float32")
            if arr.shape[1] != input_dim:
                raise ValueError(f"Expected {input_dim} features, got {arr.shape[1]}")
            label = Counter(phases).most_common(1)[0][0]
            samples.append({"features": arr, "label": label})
    finally:
        db.close()

    if not samples:
        raise RuntimeError("No patients with timeline data found in the database.")
    return samples


def synthetic_samples(input_dim: int, n: int = 64) -> list:
    return [
        {"features": torch.randn(20, input_dim).numpy(), "label": i % 4}
        for i in range(n)
    ]


def train(cfg: dict, source: str = "synthetic", max_patients: int = 0):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = HSFEncoder(
        input_dim=cfg["input_dim"],
        hidden_dim=cfg["hidden_dim"],
        embed_dim=cfg["embed_dim"],
        num_layers=cfg["num_layers"],
    ).to(device)

    if source == "db":
        samples = load_db_samples(cfg["input_dim"], max_patients=max_patients)
        print(f"Loaded {len(samples)} patient sequences from the database.")
    else:
        samples = synthetic_samples(cfg["input_dim"])
        print(f"Using {len(samples)} synthetic sequences.")

    dataset = HormonalSequenceDataset(samples)
    loader  = DataLoader(dataset, batch_size=cfg["batch_size"], shuffle=True, collate_fn=collate_fn)

    classifier = nn.Linear(cfg["embed_dim"], 5).to(device)
    optimizer  = torch.optim.AdamW(
        list(model.parameters()) + list(classifier.parameters()),
        lr=cfg["lr"], weight_decay=1e-4
    )

    for epoch in range(cfg["epochs"]):
        model.train()
        total_loss = 0.0
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            emb, _ = model(x)
            logits  = classifier(emb)

            loss_cls  = F.cross_entropy(logits, y, ignore_index=-1)
            loss_cont = contrastive_loss(emb, y)
            loss      = loss_cls + 0.3 * loss_cont

            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item()

        print(f"Epoch {epoch+1}/{cfg['epochs']}  loss={total_loss/len(loader):.4f}")

    os.makedirs(WEIGHTS_DIR, exist_ok=True)
    out_path = os.path.join(WEIGHTS_DIR, f"hsf_{cfg['embed_dim']}d.pt")
    torch.save(model.state_dict(), out_path)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the HSF encoder.")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Path to config.yaml")
    parser.add_argument(
        "--source", choices=["synthetic", "db"], default="synthetic",
        help="Training data source: 'db' pulls real sequences from the backend database.",
    )
    parser.add_argument(
        "--max-patients", type=int, default=0,
        help="Cap the number of DB patient sequences (0 = all). Useful for a quick checkpoint.",
    )
    parser.add_argument(
        "--epochs", type=int, default=0,
        help="Override the epoch count from config.yaml (0 = use config value).",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.epochs > 0:
        cfg["epochs"] = args.epochs
    train(cfg, source=args.source, max_patients=args.max_patients)
