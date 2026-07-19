"""Tests for the HSF encoder architecture (skipped if torch is unavailable)."""
import os
import sys

import pytest

from app.core.config import settings

torch = pytest.importorskip("torch")

if settings.ML_SRC_DIR not in sys.path:
    sys.path.insert(0, settings.ML_SRC_DIR)


def test_hsf_encoder_output_shape_and_norm():
    from models import HSFEncoder

    model = HSFEncoder(input_dim=9, hidden_dim=32, embed_dim=settings.EMBEDDING_DIM)
    model.eval()
    with torch.no_grad():
        x = torch.randn(2, 10, 9)  # (batch=2, T=10, features=9)
        embedding, weights = model(x)

    assert embedding.shape == (2, settings.EMBEDDING_DIM)
    # embeddings are L2-normalized
    norms = embedding.norm(dim=-1)
    assert torch.allclose(norms, torch.ones(2), atol=1e-5)
    # attention weights sum to 1 over the time dimension
    assert weights.shape == (2, 10)
    assert torch.allclose(weights.sum(dim=-1), torch.ones(2), atol=1e-5)


def test_ml_src_dir_is_valid():
    assert os.path.isdir(settings.ML_SRC_DIR)
    assert os.path.exists(os.path.join(settings.ML_SRC_DIR, "models.py"))
