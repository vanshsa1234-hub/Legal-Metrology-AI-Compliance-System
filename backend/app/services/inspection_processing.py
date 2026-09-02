"""
Legal Lens - Inspection Processing (shared by sync endpoint + Celery task)

Runs OCR extraction, rule evaluation, and PDF report generation for one
inspection. Session-agnostic so the same function works whether it's
called inline from a FastAPI request (backend/app/api/inspections.py)
or from a Celery worker (backend/app/workers/tasks.py) with its own
DB session. See docs/PRODUCTION_READINESS_PRD.md Phase 4.
"""
from sqlalchemy.orm import Session
from ..core.config import REPORTS_DIR
from ..models import Inspection, InspectionImage, ExtractedDeclaration, ComplianceResult, Product, Report, User
from .ocr_service import OCRService
from .rule_engine import RuleEngine
from .report_service import ReportService
from .audit_service import log_event
from .storage import storage


def next_report_code(db: Session) -> str:
    count = db.query(Report).count() + 1
    return f"LL-RPT-2026-{count:04d}"


def run_inspection_processing(db: Session, inspection_id: int, barcode: str = None) -> Inspection:
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise ValueError(f"Inspection {inspection_id} not found")

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

    no_issue_cnt = review_cnt = non_comp_cnt = 0
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
        overall = ins_status = "Potential Non-Compliance"
    elif review_cnt > 0:
        overall = ins_status = "Review Required"
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

    report_code = next_report_code(db)
    try:
        pdf_path = ReportService.generate_inspection_pdf(
            report_code=report_code,
            inspection=inspection,
            product=product,
            declarations=saved_decs,
            compliance_results=saved_results,
            output_dir=REPORTS_DIR
        )
        report_key = f"reports/{report_code}.pdf"
        storage.save_local_file(pdf_path, report_key)
        db.add(Report(
            report_code=report_code,
            inspection_id=inspection.id,
            user_id=inspection.user_id,
            file_path=report_key,
            file_name=f"{report_code}.pdf",
            summary=f"Automated compliance report for {product.product_name}. Result: {overall} ({non_comp_cnt} issues, {review_cnt} reviews)."
        ))
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
