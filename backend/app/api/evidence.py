"""
Legal Lens - Evidence API
Exposes the captured product images tied to one inspection.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import InspectionImage
from ..schemas import InspectionImageOut
from ..services.storage import storage

router = APIRouter(prefix="/api/evidence", tags=["Evidence"])


@router.get("/inspection/{inspection_id}", response_model=List[InspectionImageOut])
def get_inspection_evidence(inspection_id: int, db: Session = Depends(get_db)):
    return (
        db.query(InspectionImage)
        .filter(InspectionImage.inspection_id == inspection_id)
        .all()
    )


@router.get("/{image_id}/file")
def get_evidence_file(image_id: int, db: Session = Depends(get_db)):
    """
    Redirects to the actual image, regardless of storage backend: a
    local /uploads/... path, or a time-limited presigned S3/MinIO URL
    (backend/app/services/storage.py). Kept as its own tiny endpoint
    rather than exposing a raw URL on InspectionImageOut, since a
    presigned URL expires and shouldn't be cached in an API response.
    """
    image = db.query(InspectionImage).filter(InspectionImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return RedirectResponse(storage.url(image.file_path))
