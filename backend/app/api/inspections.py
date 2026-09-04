"""
Legal Lens - Inspection Lifecycle & Processing API

This is the orchestrator: it ties together image evidence, OCR
extraction, the deterministic rule engine, and PDF report generation
into one inspection lifecycle. It intentionally stays atomic (rather
than being split further into services) because /process is a single
transaction from the caller's point of view - extract, evaluate, and
report either all happen together or the inspection is left in a
partial state to retry.

Related, more granular read-only views live in:
  - api/images.py            (image upload)
  - api/ocr.py                (barcode + extraction preview)
  - api/declarations.py       (extracted fields for one inspection)
  - api/compliance.py         (rule results for one inspection)
  - api/evidence.py           (images for one inspection)
  - api/violations.py         (non-compliant results across inspections)
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..core.config import REPORTS_DIR
from ..models import Inspection, Product, ExtractedDeclaration, ComplianceResult, Report, User
from ..schemas import InspectionOut, InspectionCreate
from ..services.report_service import ReportService
from ..services.audit_service import log_event
from ..services.inspection_processing import next_report_code
from ..services.storage import storage
from ..workers.tasks import process_inspection_task
from ..workers.celery_app import celery_app
from ..core.deps import get_current_user, require_roles

router = APIRouter(prefix="/api/inspections", tags=["Inspections"])


def generate_inspection_code(db: Session) -> str:
    count = db.query(Inspection).count() + 1
    return f"LL-INS-2026-{count:04d}"


@router.post("", response_model=InspectionOut)
def create_inspection(
    data: InspectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    code = generate_inspection_code(db)
    inspection = Inspection(
        inspection_code=code,
        user_id=current_user.id,
        barcode=data.barcode,
        product_name=data.product_name or "Pending Scan",
        brand=data.brand or "Pending Extraction",
        category=data.category or "Packaged Food",
        status="Processing",
        overall_result="Review Required"
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)

    log_event(
        db=db,
        user_email=current_user.email,
        user_role=current_user.role,
        action="Inspection Created",
        entity_type="Inspection",
        entity_id=code,
        details=f"Initialized inspection session for barcode: {data.barcode or 'Manual'}"
    )

    return inspection


@router.post("/{inspection_id}/process", response_model=InspectionOut)
def process_inspection(
    inspection_id: int,
    barcode: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Runs OCR extraction + rule evaluation for one inspection.

    Dispatches to a Celery task (backend/app/workers/tasks.py). With no
    REDIS_URL configured (local/dev/tests), the task runs eagerly inline
    and this call still returns the finished inspection, exactly as
    before Phase 4. With REDIS_URL set (docker-compose with a worker),
    a separate process does the work and the client polls
    GET /{inspection_id} for status until it leaves "Processing".
    """
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    process_inspection_task.delay(inspection_id, barcode)

    if celery_app.conf.task_always_eager:
        db.refresh(inspection)  # eager mode already ran the task above; pick up its writes
        return inspection

    inspection.status = "Processing"
    db.commit()
    db.refresh(inspection)
    return inspection


@router.get("", response_model=List[InspectionOut])
def list_inspections(
    user_id: Optional[int] = None,
    result_filter: Optional[str] = None,
    pending_review: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Citizens only ever see their own inspections; officers/admins may
    filter by any user_id.

    pending_review=true (officer/admin only) is the Phase 12
    (docs/PRODUCTION_READINESS_PRD.md) "Final Evidence -> Human Review"
    queue: every Review Required / Potential Non-Compliance inspection
    still awaiting an officer verdict, independent of whether a citizen
    has separately filed a complaint about it (POST /api/requests) -
    that path existed before, this surfaces the ones nobody complained
    about yet too.
    """
    query = db.query(Inspection)
    if current_user.role == "user":
        query = query.filter(Inspection.user_id == current_user.id)
    elif user_id:
        query = query.filter(Inspection.user_id == user_id)
    if result_filter and result_filter != "All":
        query = query.filter(Inspection.overall_result == result_filter)
    if pending_review:
        if current_user.role not in ("officer", "admin"):
            raise HTTPException(status_code=403, detail="Requires role: officer or admin")
        query = query.filter(
            Inspection.overall_result.in_(["Review Required", "Potential Non-Compliance"]),
            Inspection.officer_review_status == "Pending",
        )

    return query.order_by(Inspection.created_at.desc()).all()


@router.get("/{inspection_id}", response_model=InspectionOut)
def get_inspection(inspection_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    if current_user.role == "user" and inspection.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this inspection")
    return inspection


@router.post("/{inspection_id}/review", response_model=InspectionOut, dependencies=[Depends(require_roles("officer", "admin"))])
def record_officer_review(
    inspection_id: int,
    verdict: str = Form(...),
    remarks: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Phase 12 (docs/PRODUCTION_READINESS_PRD.md): the "Human Review"
    step directly on an inspection's assembled evidence (OCR output +
    rule-engine results), independent of the citizen-complaint flow in
    api/cases.py. verdict must be "Verified" or "Non-Compliance Confirmed".
    """
    if verdict not in ("Verified", "Non-Compliance Confirmed"):
        raise HTTPException(status_code=400, detail="verdict must be 'Verified' or 'Non-Compliance Confirmed'")

    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    inspection.officer_review_status = verdict
    db.commit()
    db.refresh(inspection)

    log_event(
        db=db,
        user_email=current_user.email,
        user_role=current_user.role,
        action="Officer Review Recorded",
        entity_type="Inspection",
        entity_id=inspection.inspection_code,
        details=f"Verdict: {verdict}" + (f" - {remarks}" if remarks else "")
    )
    return inspection


@router.get("/{inspection_id}/report")
def download_inspection_report(inspection_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    inspection_for_check = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection_for_check:
        raise HTTPException(status_code=404, detail="Inspection not found")
    if current_user.role == "user" and inspection_for_check.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this inspection's report")

    report = db.query(Report).filter(Report.inspection_id == inspection_id).first()
    resolved_path = storage.local_path(report.file_path) if report else None

    if not resolved_path:
        inspection = inspection_for_check
        product = db.query(Product).filter(Product.id == inspection.product_id).first()
        decs = db.query(ExtractedDeclaration).filter(ExtractedDeclaration.inspection_id == inspection_id).all()
        results = db.query(ComplianceResult).filter(ComplianceResult.inspection_id == inspection_id).all()

        report_code = next_report_code(db)
        pdf_path = ReportService.generate_inspection_pdf(
            report_code=report_code,
            inspection=inspection,
            product=product,
            declarations=decs,
            compliance_results=results,
            output_dir=REPORTS_DIR
        )
        report_key = f"reports/{report_code}.pdf"
        storage.save_local_file(pdf_path, report_key)
        report = Report(
            report_code=report_code,
            inspection_id=inspection.id,
            user_id=inspection.user_id,
            file_path=report_key,
            file_name=f"{report_code}.pdf",
            summary="Generated compliance PDF report."
        )
        db.add(report)
        db.commit()
        resolved_path = storage.local_path(report_key)

    return FileResponse(
        path=resolved_path,
        filename=report.file_name,
        media_type="application/pdf"
    )
