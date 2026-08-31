"""
Legal Lens - OCR / Barcode API

Two responsibilities:
  1. Let the frontend attach/update a barcode on an in-progress inspection.
  2. Preview what OCRService would extract for a barcode, without
     writing anything to the database - useful for the frontend's
     "scan preview" step before committing to a full inspection.

See services/ocr_service.py for the current (demo-catalog) extraction
implementation and its documented limitations.
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Inspection
from ..services.ocr_service import OCRService

router = APIRouter(prefix="/api/inspections", tags=["OCR"])
preview_router = APIRouter(prefix="/api/ocr", tags=["OCR"])


@router.post("/{inspection_id}/barcode")
def set_inspection_barcode(
    inspection_id: int,
    barcode: str = Form(...),
    db: Session = Depends(get_db)
):
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    inspection.barcode = barcode.strip()
    db.commit()

    return {
        "status": "success",
        "barcode": inspection.barcode,
        "inspection_code": inspection.inspection_code
    }


@preview_router.get("/preview")
def preview_extraction(barcode: str):
    """
    Preview extracted label data for a barcode before committing it to
    an inspection. Uses the same OCRService the main pipeline uses.
    """
    return OCRService.extract_product_data(images=[], barcode=barcode)
