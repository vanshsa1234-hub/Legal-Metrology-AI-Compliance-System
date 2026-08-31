"""
Legal Lens - Dashboard / Analytics Metrics API

Note: URL prefix is kept as /api/dashboard (not /api/analytics) so the
existing frontend, which already calls /api/dashboard/user and
/api/dashboard/admin, keeps working unchanged.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Inspection, Request, Product, LegalRule

router = APIRouter(prefix="/api/dashboard", tags=["Analytics"])


@router.get("/user")
def get_user_dashboard(user_id: int = 1, db: Session = Depends(get_db)):
    """Get metrics for consumer user dashboard."""
    total_scanned = db.query(Inspection).filter(Inspection.user_id == user_id).count()
    total_reports = total_scanned  # Every completed inspection has a report
    requests_raised = db.query(Request).filter(Request.user_id == user_id).count()

    recent_inspections = (
        db.query(Inspection)
        .filter(Inspection.user_id == user_id)
        .order_by(Inspection.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "stats": {
            "products_scanned": total_scanned,
            "reports_generated": total_reports,
            "requests_raised": requests_raised
        },
        "recent_inspections": [
            {
                "id": ins.id,
                "inspection_code": ins.inspection_code,
                "product_name": ins.product_name or "Packaged Commodity",
                "brand": ins.brand or "Brand",
                "category": ins.category or "Packaged Food",
                "status": ins.status,
                "overall_result": ins.overall_result,
                "date": ins.created_at.strftime("%d %b %Y"),
                "rules_checked": ins.rules_checked_count,
                "non_compliance_count": ins.non_compliance_count
            }
            for ins in recent_inspections
        ]
    }


@router.get("/admin")
def get_admin_dashboard(db: Session = Depends(get_db)):
    """Comprehensive stats and chart series for the officer/admin dashboard."""
    total_inspections = db.query(Inspection).count()
    no_issue_count = db.query(Inspection).filter(Inspection.overall_result == "No Issue Detected").count()
    review_required_count = db.query(Inspection).filter(Inspection.overall_result == "Review Required").count()
    non_compliance_count = db.query(Inspection).filter(Inspection.overall_result == "Potential Non-Compliance").count()

    total_requests = db.query(Request).count()
    cases_under_review = db.query(Request).filter(Request.status == "Under Review").count()
    cases_action_initiated = db.query(Request).filter(Request.status == "Action Initiated").count()

    total_products = db.query(Product).count()
    total_rules = db.query(LegalRule).count()

    # Category Breakdown for Chart.js
    category_counts = {}
    for p in db.query(Product).all():
        cat = p.category or "Other"
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Status distribution for Doughnut Chart
    compliance_distribution = {
        "labels": ["No Issue Detected", "Review Required", "Potential Non-Compliance"],
        "data": [
            max(no_issue_count, 1),
            max(review_required_count, 1),
            max(non_compliance_count, 1)
        ],
        "colors": ["#16a34a", "#eab308", "#dc2626"]
    }

    # NOTE: this weekly trend series is placeholder display data, not a
    # real query over inspection timestamps yet. Flagged here (rather
    # than hidden) so it's easy to find and wire up to a real
    # GROUP BY day query later. See docs/ROADMAP.md.
    inspections_trend = {
        "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "data": [12, 19, 15, 25, 22, 30, max(total_inspections, 28)]
    }

    return {
        "stats": {
            "total_inspections": total_inspections,
            "no_issue_count": no_issue_count,
            "review_required_count": review_required_count,
            "non_compliance_count": non_compliance_count,
            "requests_raised": total_requests,
            "cases_under_review": cases_under_review + cases_action_initiated,
            "total_products": total_products,
            "total_rules": total_rules
        },
        "charts": {
            "compliance_distribution": compliance_distribution,
            "inspections_trend": inspections_trend,
            "categories": {
                "labels": list(category_counts.keys()) or ["Packaged Food", "Packaged Water", "Probiotic Foods"],
                "data": list(category_counts.values()) or [3, 1, 1]
            }
        }
    }
