"""
Legal Lens - Evidence API
Exposes the captured product images tied to one inspection.
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import InspectionImage
from ..schemas import InspectionImageOut

router = APIRouter(prefix="/api/evidence", tags=["Evidence"])


@router.get("/inspection/{inspection_id}", response_model=List[InspectionImageOut])
def get_inspection_evidence(inspection_id: int, db: Session = Depends(get_db)):
    return (
        db.query(InspectionImage)
        .filter(InspectionImage.inspection_id == inspection_id)
        .all()
    )
