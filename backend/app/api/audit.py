"""
Legal Lens - Immutable Audit Trail API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import AuditLog
from ..schemas import AuditLogOut
from ..core.deps import require_roles

router = APIRouter(prefix="/api/audit", tags=["Audit Trail"])

@router.get("", response_model=List[AuditLogOut], dependencies=[Depends(require_roles("officer", "admin"))])
def get_audit_trail(
    entity_type: Optional[str] = None,
    user_role: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if entity_type and entity_type != "All":
        query = query.filter(AuditLog.entity_type == entity_type)
    if user_role and user_role != "All":
        query = query.filter(AuditLog.user_role == user_role)

    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
