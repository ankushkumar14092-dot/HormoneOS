import numpy as np
import torch
from torch.utils.data import Dataset
from torch.nn.utils.rnn import pad_sequence


FEATURE_COLS = [
    "heart_rate", "active_minutes", "computed_temperature",
    "vo2_max", "estrogen", "progesterone", "lh", "fsh", "glucose",
]

PHASE_MAP = {"menstrual": 0, "follicular": 1, "ovulatory": 2, "luteal": 3, "unknown": 4}


class HormonalSequenceDataset(Dataset):
    """
    Expects a list of dicts, each with:
      - 'features': np.ndarray of shape (T, 9)
      - 'label':    int phase label (optional)
    """

    def __init__(self, samples: list):
        self.samples = samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        s = self.samples[idx]
        x = torch.tensor(s["features"], dtype=torch.float32)
        y = torch.tensor(s.get("label", -1), dtype=torch.long)
        return x, y


def collate_fn(batch):
    """Pad variable-length sequences to the longest in the batch."""
    seqs, labels = zip(*batch)
    padded = pad_sequence(seqs, batch_first=True, padding_value=0.0)
    return padded, torch.stack(labels)
