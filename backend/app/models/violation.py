"""
Legal Lens - Violation Domain

Design note: a "violation" is not a separate database table. It is a
ComplianceResult whose status is POTENTIAL NON-COMPLIANCE. Rather than
duplicating the compliance_results table under a second name, this
module exposes that same model under a domain-friendly alias plus a
small query helper, so the API layer (api/violations.py) and the
dashboard can talk about "violations" without redundant storage.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from .compliance import ComplianceResult, STATUS_NON_COMPLIANCE

# Domain alias: a Violation *is* a ComplianceResult, filtered by status.
Violation = ComplianceResult


def get_violations(db: Session, inspection_id: Optional[int] = None) -> List[ComplianceResult]:
    """Return all compliance results flagged as POTENTIAL NON-COMPLIANCE."""
    query = db.query(ComplianceResult).filter(ComplianceResult.status == STATUS_NON_COMPLIANCE)
    if inspection_id is not None:
        query = query.filter(ComplianceResult.inspection_id == inspection_id)
    return query.order_by(ComplianceResult.created_at.desc()).all()
