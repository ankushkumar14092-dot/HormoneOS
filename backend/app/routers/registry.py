import io, json, csv
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.repos import EmbeddingRepo
from app.schemas.schemas import EmbeddingOut
from app.models.models import Timeline

router = APIRouter(prefix="/api/v1/registry", tags=["registry"])


def _to_out(e) -> EmbeddingOut:
    tl = e.timeline
    return EmbeddingOut(
        id=e.id,
        timeline_id=e.timeline_id,
        patient_id=tl.patient_id if tl else 0,
        model_version=e.model_version,
        vector=e.vector,
        created_at=e.created_at,
    )


@router.get("/search", response_model=list[EmbeddingOut])
def search(
    patient_id:    Optional[int] = Query(None),
    model_version: Optional[str] = Query(None),
    dataset_id:    Optional[int] = Query(None),
    limit:         int           = Query(200, le=2000),
    db:            Session       = Depends(get_db),
):
    results = EmbeddingRepo(db).search(
        patient_id=patient_id,
        model_version=model_version,
        dataset_id=dataset_id,
        limit=limit
    )
    return [_to_out(e) for e in results]


@router.get("/download")
def download(
    fmt:           str           = Query("json", regex="^(json|csv)$"),
    patient_id:    Optional[int] = Query(None),
    model_version: Optional[str] = Query(None),
    db:            Session       = Depends(get_db),
):
    results = EmbeddingRepo(db).search(patient_id=patient_id, model_version=model_version, limit=10000)
    rows    = [_to_out(e).model_dump() for e in results]

    if fmt == "json":
        content = json.dumps(rows, default=str)
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=representations.json"},
        )

    # CSV
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=[k for k in rows[0] if k != "vector"])
        writer.writeheader()
        for r in rows:
            r.pop("vector", None)
            writer.writerow(r)
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=representations.csv"},
    )
