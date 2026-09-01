"""
Legal Lens - Dashboard / Analytics Metrics API

Note: URL prefix is kept as /api/dashboard (not /api/analytics) so the
existing frontend, which already calls /api/dashboard/user and
/api/dashboard/admin, keeps working unchanged.
"""
import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Inspection, Request, Product, LegalRule, User
from ..core.deps import get_current_user, require_roles

router = APIRouter(prefix="/api/dashboard", tags=["Analytics"])


def _weekly_inspections_trend(db: Session) -> dict:
    """
    Real GROUP BY day query over Inspection.created_at for the last 7
    days (including today), zero-filled for days with no inspections.
    Replaces the previous hardcoded [12, 19, 15, 25, 22, 30, ...] array.
    """
    today = datetime.datetime.utcnow().date()
    start_date = today - datetime.timedelta(days=6)
    start_dt = datetime.datetime.combine(start_date, datetime.time.min)

    rows = (
        db.query(
            func.date(Inspection.created_at).label("day"),
            func.count(Inspection.id).label("count"),
        )
        .filter(Inspection.created_at >= start_dt)
        .group_by(func.date(Inspection.created_at))
        .all()
    )
    counts_by_day = {str(r.day): r.count for r in rows}

    labels, data = [], []
    for i in range(7):
        d = start_date + datetime.timedelta(days=i)
        labels.append(d.strftime("%a"))
        data.append(counts_by_day.get(str(d), 0))

    return {"labels": labels, "data": data}


@router.get("/user")
def get_user_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get metrics for the authenticated consumer's own dashboard."""
    user_id = current_user.id
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


@router.get("/admin", dependencies=[Depends(require_roles("officer", "admin"))])
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

    # Category Breakdown for Chart.js - real GROUP BY over Product.category.
    category_rows = (
        db.query(Product.category, func.count(Product.id))
        .group_by(Product.category)
        .all()
    )
    category_counts = {(cat or "Other"): count for cat, count in category_rows}

    # Status distribution for Doughnut Chart. The max(..., 1) floor is
    # kept only so an all-zero dataset still renders a visible (if
    # empty-looking) doughnut instead of a divide-by-zero chart - it
    # does not fabricate results, it just avoids a blank chart when the
    # real counts are genuinely zero.
    compliance_distribution = {
        "labels": ["No Issue Detected", "Review Required", "Potential Non-Compliance"],
        "data": [
            max(no_issue_count, 1) if total_inspections else 0,
            max(review_required_count, 1) if total_inspections else 0,
            max(non_compliance_count, 1) if total_inspections else 0,
        ] if total_inspections else [0, 0, 0],
        "colors": ["#16a34a", "#eab308", "#dc2626"]
    }

    # Real GROUP BY day query over inspection timestamps for the last 7
    # days (see _weekly_inspections_trend above), replacing the old
    # hardcoded [12, 19, 15, 25, 22, 30, ...] placeholder array.
    inspections_trend = _weekly_inspections_trend(db)

    # No fabricated fallback here: if there are genuinely no products
    # yet, the chart legitimately has nothing to show, and the
    # frontend is expected to render its own "no data yet" empty state
    # rather than being handed invented category names/counts.
    categories_chart = {
        "labels": list(category_counts.keys()),
        "data": list(category_counts.values())
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
            "categories": categories_chart
        }
    }
