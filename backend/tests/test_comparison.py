"""Tests for the pure math helpers in the comparison service."""
import numpy as np

from app.services.comparison import _cosine, _dtw


def test_cosine_identical_vectors():
    a = np.array([1.0, 2.0, 3.0])
    assert np.isclose(_cosine(a, a), 1.0)


def test_cosine_orthogonal_vectors():
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 1.0])
    assert np.isclose(_cosine(a, b), 0.0)


def test_cosine_zero_vector_is_safe():
    a = np.zeros(3)
    b = np.array([1.0, 2.0, 3.0])
    assert _cosine(a, b) == 0.0


def test_dtw_identical_sequences_is_zero():
    seq = np.array([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]])
    assert np.isclose(_dtw(seq, seq), 0.0)


def test_dtw_is_symmetric_and_positive():
    a = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
    b = np.array([[0.0, 0.0], [2.0, 2.0]])
    d_ab = _dtw(a, b)
    d_ba = _dtw(b, a)
    assert d_ab > 0
    assert np.isclose(d_ab, d_ba)
