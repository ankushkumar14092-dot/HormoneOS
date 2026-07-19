import numpy as np
from sqlalchemy.orm import Session
from app.repositories.repos import EmbeddingRepo
from app.schemas.schemas import CompareOut
from app.services.llm_service import compare_narrative


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _dtw(A: np.ndarray, B: np.ndarray) -> float:
    """Naive O(n*m) DTW on L2 distance between embedding vectors."""
    n, m = len(A), len(B)
    cost = np.full((n + 1, m + 1), np.inf)
    cost[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d = np.linalg.norm(A[i - 1] - B[j - 1])
            cost[i, j] = d + min(cost[i - 1, j], cost[i, j - 1], cost[i - 1, j - 1])
    return float(cost[n, m])


def compare_patients(db: Session, patient_a_id: int, patient_b_id: int) -> CompareOut:
    repo = EmbeddingRepo(db)
    embs_a = repo.get_by_patient(patient_a_id)
    embs_b = repo.get_by_patient(patient_b_id)

    if not embs_a or not embs_b:
        return CompareOut(
            patient_a_id=patient_a_id,
            patient_b_id=patient_b_id,
            cosine_similarity=0.0,
            dtw_distance=0.0,
            similarity_score=0.0,
        )

    A = np.array([e.vector for e in embs_a], dtype=np.float32)
    B = np.array([e.vector for e in embs_b], dtype=np.float32)

    # Mean-pool for cosine
    cosine = _cosine(A.mean(axis=0), B.mean(axis=0))

    # DTW on full sequences (cap at 50 steps each for speed)
    dtw_dist = _dtw(A[:50], B[:50])

    # Normalise DTW to [0,1] similarity: sigmoid-like decay
    dtw_sim = float(1.0 / (1.0 + dtw_dist / max(len(A), len(B))))

    similarity_score = round(0.6 * ((cosine + 1) / 2) + 0.4 * dtw_sim, 4)

    result = CompareOut(
        patient_a_id=patient_a_id,
        patient_b_id=patient_b_id,
        cosine_similarity=round(cosine, 4),
        dtw_distance=round(dtw_dist, 4),
        similarity_score=min(max(similarity_score, 0.0), 1.0),
        narrative=compare_narrative(
            patient_a_id, patient_b_id,
            round(cosine, 4), round(dtw_dist, 4),
            min(max(similarity_score, 0.0), 1.0),
        ),
    )
    return result
