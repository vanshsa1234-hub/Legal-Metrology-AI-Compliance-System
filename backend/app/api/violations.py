"""
Legal Lens - Violations API

Read-only, cross-inspection view of confirmed/flagged compliance
violations, for officer triage without paging through every
inspection individually. See models/violation.py for why this reuses
ComplianceResult instead of a separate table.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import get_violations
from ..schemas import ViolationOut

router = APIRouter(prefix="/api/violations", tags=["Violations"])


@router.get("", response_model=List[ViolationOut])
def list_violations(inspection_id: Optional[int] = None, db: Session = Depends(get_db)):
    """List all compliance results flagged as POTENTIAL NON-COMPLIANCE."""
    return get_violations(db, inspection_id=inspection_id)
