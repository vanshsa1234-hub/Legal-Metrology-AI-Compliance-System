"""
Legal Lens - Declarations API
Exposes the extracted label fields (MRP, net quantity, manufacturer,
etc.) tied to one inspection.
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ExtractedDeclaration
from ..schemas import ExtractedDeclarationOut

router = APIRouter(prefix="/api/declarations", tags=["Declarations"])


@router.get("/inspection/{inspection_id}", response_model=List[ExtractedDeclarationOut])
def get_inspection_declarations(inspection_id: int, db: Session = Depends(get_db)):
    return (
        db.query(ExtractedDeclaration)
        .filter(ExtractedDeclaration.inspection_id == inspection_id)
        .all()
    )
