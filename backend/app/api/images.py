"""
Legal Lens - Inspection Image Upload API

Split out from the inspection orchestrator so image capture/storage is
its own concern. Shares the /api/inspections prefix so the existing
frontend calls (POST /api/inspections/{id}/images) keep working
unchanged.
"""
import os
import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Inspection, InspectionImage
from ..services.ocr_service import OCRService
from ..services.storage import storage

router = APIRouter(prefix="/api/inspections", tags=["Images"])


@router.post("/{inspection_id}/images")
async def upload_inspection_images(
    inspection_id: int,
    image_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a front/back label photo for an inspection and score its quality."""
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection session not found")

    file_ext = os.path.splitext(file.filename)[1] or ".jpg"
    safe_filename = f"{inspection.inspection_code}_{image_type}_{int(datetime.datetime.utcnow().timestamp())}{file_ext}"
    key = f"images/products/{safe_filename}"

    storage.save(file.file, key)

    quality_result = OCRService.evaluate_image_quality(key)

    existing_img = (
        db.query(InspectionImage)
        .filter(InspectionImage.inspection_id == inspection_id, InspectionImage.image_type == image_type)
        .first()
    )
    if existing_img:
        existing_img.file_path = key
        existing_img.file_name = safe_filename
        existing_img.quality_score = quality_result["score"]
        existing_img.quality_label = quality_result["label"]
    else:
        new_img = InspectionImage(
            inspection_id=inspection_id,
            image_type=image_type,
            file_path=key,
            file_name=safe_filename,
            quality_score=quality_result["score"],
            quality_label=quality_result["label"]
        )
        db.add(new_img)

    db.commit()

    return {
        "status": "success",
        "image_type": image_type,
        "file_name": safe_filename,
        "file_url": storage.url(key),
        "quality_score": quality_result["score"],
        "quality_label": quality_result["label"],
        "details": quality_result["details"]
    }
