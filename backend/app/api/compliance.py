"""
Legal Lens - Compliance API
Exposes the full set of rule-engine results (all statuses, not just
violations) tied to one inspection.
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ComplianceResult
from ..schemas import ComplianceResultOut

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])


@router.get("/inspection/{inspection_id}", response_model=List[ComplianceResultOut])
def get_inspection_compliance(inspection_id: int, db: Session = Depends(get_db)):
    return (
        db.query(ComplianceResult)
        .filter(ComplianceResult.inspection_id == inspection_id)
        .all()
    )
