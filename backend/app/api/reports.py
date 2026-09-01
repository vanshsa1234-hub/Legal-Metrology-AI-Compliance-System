"""
Legal Lens - Reports Repository API
"""
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Report, Inspection, Product, User
from ..schemas import ReportOut
from ..core.deps import get_current_user

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("", response_model=List[ReportOut])
def list_reports(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Citizens only ever see their own reports; officers/admins may filter by any user_id."""
    query = db.query(Report)
    if current_user.role == "user":
        query = query.filter(Report.user_id == current_user.id)
    elif user_id:
        query = query.filter(Report.user_id == user_id)
    
    reports = query.order_by(Report.created_at.desc()).all()
    results = []
    for r in reports:
        ins = db.query(Inspection).filter(Inspection.id == r.inspection_id).first()
        prod_name = ins.product_name if ins else "Packaged Product"
        overall_res = ins.overall_result if ins else "Review Required"
        results.append({
            "id": r.id,
            "report_code": r.report_code,
            "inspection_id": r.inspection_id,
            "file_path": r.file_path,
            "file_name": r.file_name,
            "summary": r.summary,
            "created_at": r.created_at,
            "product_name": prod_name,
            "overall_result": overall_res
        })
    return results

@router.get("/{report_id}/download")
def download_report_by_id(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report PDF file not found")
    return FileResponse(
        path=report.file_path,
        filename=report.file_name,
        media_type="application/pdf"
    )
