from __future__ import annotations
from typing import Optional
from openai import OpenAI
from app.core.config import settings

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def _chat(system: str, user: str, max_tokens: int = 400) -> str:
    try:
        resp = _get_client().chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            max_tokens=max_tokens,
            temperature=0.4,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[LLM unavailable: {e}]"


# ── 1. Explain representation ─────────────────────────────────────────────────

def explain_narrative(
    patient_id: int,
    attention_weights: list[float],
    feature_names: list[str],
    top_n: int = 4,
) -> str:
    """
    Given per-timestep attention weights and feature names, ask GPT-4o to
    narrate which signals are driving the HSF representation in plain English.
    """
    # Build top-N most attended timesteps summary
    indexed = sorted(enumerate(attention_weights), key=lambda x: x[1], reverse=True)[:top_n]
    top_steps = [
        f"timestep {i+1} (attention={w:.3f})"
        for i, w in indexed
    ]

    # Per-feature mean contribution (weight × feature index proxy)
    feature_summary = ", ".join(
        f"{name}" for name in feature_names
    )

    user_msg = (
        f"Patient ID: {patient_id}\n"
        f"The HSF model assigned highest attention to: {', '.join(top_steps)}.\n"
        f"The input features are: {feature_summary}.\n\n"
        f"In 3–4 sentences, explain what this attention pattern likely means "
        f"for this patient's hormonal health representation. Be specific about "
        f"which biological signals are most informative and why."
    )

    return _chat(
        system=(
            "You are a women's health research assistant interpreting outputs from "
            "the Hormone State Foundation (HSF), a GRU-based temporal encoder trained "
            "on menstrual cycle wearable and hormonal data. Explain model attention "
            "patterns in clear, scientifically grounded language suitable for researchers."
        ),
        user=user_msg,
        max_tokens=250,
    )


# ── 2. Compare narrative ──────────────────────────────────────────────────────

def compare_narrative(
    patient_a_id: int,
    patient_b_id: int,
    cosine_similarity: float,
    dtw_distance: float,
    similarity_score: float,
) -> str:
    """
    Given comparison metrics between two patients, ask GPT-4o to write a
    clinical summary of what the similarity means.
    """
    user_msg = (
        f"Patient A (ID {patient_a_id}) vs Patient B (ID {patient_b_id}):\n"
        f"- Cosine similarity of mean HSF embeddings: {cosine_similarity:.4f}\n"
        f"- DTW distance across embedding sequences: {dtw_distance:.4f}\n"
        f"- Combined similarity score (0–1): {similarity_score:.4f}\n\n"
        f"In 3–4 sentences, interpret what this similarity score means clinically. "
        f"Discuss whether these patients likely share similar hormonal trajectory "
        f"patterns, and what that could imply for research grouping or personalised "
        f"health modelling."
    )

    return _chat(
        system=(
            "You are a women's health research assistant interpreting patient similarity "
            "scores from the HormoneOS Hormone State Foundation (HSF). Similarity is "
            "computed via cosine similarity of 128-d embeddings and DTW alignment of "
            "longitudinal hormonal sequences. Provide concise, scientifically grounded "
            "interpretations suitable for clinical researchers."
        ),
        user=user_msg,
        max_tokens=250,
    )


# ── 3. Ingestion transformation summary ──────────────────────────────────────

def ingestion_summary(
    dataset_name: str,
    n_records: int,
    n_patients: int,
    n_errors: int,
    columns_joined: list[str],
) -> str:
    """
    After ingestion completes, ask GPT-4o to auto-generate a transformation_history
    action description summarising what was done to the data.
    """
    user_msg = (
        f"Dataset: {dataset_name}\n"
        f"Records ingested: {n_records}\n"
        f"Unique patients: {n_patients}\n"
        f"Errors skipped: {n_errors}\n"
        f"CSV sources joined: {', '.join(columns_joined)}\n\n"
        f"Write a single concise sentence (max 40 words) describing this ingestion "
        f"transformation for an audit log. Include what data sources were merged, "
        f"how many records were processed, and any notable data quality notes."
    )

    return _chat(
        system=(
            "You are a data engineering assistant writing audit log entries for the "
            "HormoneOS Universal Hormonal Schema (UHS) ingestion pipeline. "
            "Write factual, concise transformation descriptions."
        ),
        user=user_msg,
        max_tokens=80,
    )
