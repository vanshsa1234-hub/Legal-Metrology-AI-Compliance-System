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
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..core.config import REPORTS_DIR
from ..models import (
    Inspection, InspectionImage, ExtractedDeclaration, ComplianceResult,
    Product, Report, User
)
from ..schemas import InspectionOut, InspectionCreate
from ..services.ocr_service import OCRService
from ..services.rule_engine import RuleEngine
from ..services.report_service import ReportService
from ..services.audit_service import log_event
from ..core.deps import get_current_user

router = APIRouter(prefix="/api/inspections", tags=["Inspections"])


def generate_inspection_code(db: Session) -> str:
    count = db.query(Inspection).count() + 1
    return f"LL-INS-2026-{count:04d}"


def generate_report_code(db: Session) -> str:
    count = db.query(Report).count() + 1
    return f"LL-RPT-2026-{count:04d}"


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
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    active_barcode = barcode or inspection.barcode or "8901234567890"
    inspection.barcode = active_barcode

    images = db.query(InspectionImage).filter(InspectionImage.inspection_id == inspection_id).all()
    img_dicts = [{"type": img.image_type, "path": img.file_path} for img in images]

    extracted = OCRService.extract_product_data(images=img_dicts, barcode=active_barcode)

    product = db.query(Product).filter(Product.barcode == active_barcode).first()
    if not product:
        product = Product(
            product_name=extracted.get("product_name", "Packaged Product"),
            brand=extracted.get("brand", "Brand"),
            category=extracted.get("category", "Packaged Food"),
            sub_category=extracted.get("sub_category", "Packaged Retail Goods"),
            manufacturer=extracted.get("manufacturer"),
            net_quantity=extracted.get("net_quantity"),
            mrp=extracted.get("mrp"),
            batch_number=extracted.get("batch_number"),
            mfg_date=extracted.get("mfg_date"),
            best_before=extracted.get("best_before"),
            consumer_care=extracted.get("consumer_care"),
            ingredients=extracted.get("ingredients"),
            veg_non_veg=extracted.get("veg_non_veg", "Vegetarian"),
            fssai_license=extracted.get("fssai_license"),
            country_of_origin=extracted.get("country_of_origin", "India"),
            barcode=active_barcode
        )
        db.add(product)
        db.commit()
        db.refresh(product)

    inspection.product_id = product.id
    inspection.product_name = product.product_name
    inspection.brand = product.brand
    inspection.category = product.category

    db.query(ExtractedDeclaration).filter(ExtractedDeclaration.inspection_id == inspection_id).delete()
    saved_decs = []
    for d in extracted.get("declarations", []):
        dec_obj = ExtractedDeclaration(
            inspection_id=inspection.id,
            field_name=d["field_name"],
            detected_value=d["detected_value"],
            confidence=d["confidence"],
            confidence_level=d["confidence_level"],
            evidence_image_type=d["evidence_image_type"],
            bounding_box=d.get("bounding_box")
        )
        db.add(dec_obj)
        saved_decs.append(dec_obj)
    db.commit()

    db.query(ComplianceResult).filter(ComplianceResult.inspection_id == inspection_id).delete()
    applicable_rules = RuleEngine.get_applicable_rules(db, category=product.category, sub_category=product.sub_category)
    eval_results = RuleEngine.evaluate_compliance(applicable_rules, extracted)

    no_issue_cnt = 0
    review_cnt = 0
    non_comp_cnt = 0
    total_conf = 0.0

    saved_results = []
    for res in eval_results:
        st = res["status"]
        if st == "NO ISSUE DETECTED":
            no_issue_cnt += 1
        elif st == "REVIEW REQUIRED":
            review_cnt += 1
        elif st == "POTENTIAL NON-COMPLIANCE":
            non_comp_cnt += 1

        total_conf += res["confidence"]

        c_obj = ComplianceResult(
            inspection_id=inspection.id,
            rule_id=res["rule_id"],
            rule_title=res["rule_title"],
            status=st,
            confidence=res["confidence"],
            evidence_type=res["evidence_type"],
            reason=res["reason"],
            what_checked=res["what_checked"],
            what_found=res["what_found"],
            why_flagged=res.get("why_flagged"),
            applicable_regulation=res["applicable_regulation"],
            clause=res.get("clause"),
            version_amendment=res.get("version_amendment")
        )
        db.add(c_obj)
        saved_results.append(c_obj)

    total_rules = len(eval_results)
    avg_conf = (total_conf / total_rules) if total_rules > 0 else 85.0

    if non_comp_cnt > 0:
        overall = "Potential Non-Compliance"
        ins_status = "Potential Non-Compliance"
    elif review_cnt > 0:
        overall = "Review Required"
        ins_status = "Review Required"
    else:
        overall = "No Issue Detected"
        ins_status = "Completed"

    inspection.status = ins_status
    inspection.overall_result = overall
    inspection.confidence_score = round(avg_conf, 1)
    inspection.rules_checked_count = total_rules
    inspection.no_issue_count = no_issue_cnt
    inspection.review_required_count = review_cnt
    inspection.non_compliance_count = non_comp_cnt
    db.commit()

    report_code = generate_report_code(db)
    try:
        pdf_path = ReportService.generate_inspection_pdf(
            report_code=report_code,
            inspection=inspection,
            product=product,
            declarations=saved_decs,
            compliance_results=saved_results,
            output_dir=REPORTS_DIR
        )
        report = Report(
            report_code=report_code,
            inspection_id=inspection.id,
            user_id=inspection.user_id,
            file_path=pdf_path,
            file_name=f"{report_code}.pdf",
            summary=f"Automated compliance report for {product.product_name}. Result: {overall} ({non_comp_cnt} issues, {review_cnt} reviews)."
        )
        db.add(report)
        db.commit()
    except Exception as e:
        print(f"PDF Generation error: {e}")

    user = db.query(User).filter(User.id == inspection.user_id).first()
    log_event(
        db=db,
        user_email=user.email if user else "user@legallens.demo",
        user_role=user.role if user else "user",
        action="Compliance Analysis Completed",
        entity_type="Inspection",
        entity_id=inspection.inspection_code,
        details=f"Evaluated {total_rules} rules. Overall Result: {overall} ({non_comp_cnt} Non-Compliance, {review_cnt} Review)"
    )

    db.refresh(inspection)
    return inspection


@router.get("", response_model=List[InspectionOut])
def list_inspections(
    user_id: Optional[int] = None,
    result_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Citizens only ever see their own inspections; officers/admins may filter by any user_id."""
    query = db.query(Inspection)
    if current_user.role == "user":
        query = query.filter(Inspection.user_id == current_user.id)
    elif user_id:
        query = query.filter(Inspection.user_id == user_id)
    if result_filter and result_filter != "All":
        query = query.filter(Inspection.overall_result == result_filter)

    return query.order_by(Inspection.created_at.desc()).all()


@router.get("/{inspection_id}", response_model=InspectionOut)
def get_inspection(inspection_id: int, db: Session = Depends(get_db)):
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection


@router.get("/{inspection_id}/report")
def download_inspection_report(inspection_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.inspection_id == inspection_id).first()
    if not report or not os.path.exists(report.file_path):
        inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
        if not inspection:
            raise HTTPException(status_code=404, detail="Inspection not found")

        product = db.query(Product).filter(Product.id == inspection.product_id).first()
        decs = db.query(ExtractedDeclaration).filter(ExtractedDeclaration.inspection_id == inspection_id).all()
        results = db.query(ComplianceResult).filter(ComplianceResult.inspection_id == inspection_id).all()

        report_code = generate_report_code(db)
        pdf_path = ReportService.generate_inspection_pdf(
            report_code=report_code,
            inspection=inspection,
            product=product,
            declarations=decs,
            compliance_results=results,
            output_dir=REPORTS_DIR
        )
        report = Report(
            report_code=report_code,
            inspection_id=inspection.id,
            user_id=inspection.user_id,
            file_path=pdf_path,
            file_name=f"{report_code}.pdf",
            summary="Generated compliance PDF report."
        )
        db.add(report)
        db.commit()

    return FileResponse(
        path=report.file_path,
        filename=report.file_name,
        media_type="application/pdf"
    )
