"""
Legal Lens - Audit Logging Service
"""
import datetime
from sqlalchemy.orm import Session
from ..models import AuditLog

def log_event(
    db: Session,
    user_email: str,
    user_role: str,
    action: str,
    entity_type: str,
    entity_id: str = None,
    details: str = None,
    ip_address: str = "127.0.0.1"
):
    """
    Record an immutable event in the audit trail.
    """
    try:
        log_entry = AuditLog(
            timestamp=datetime.datetime.utcnow(),
            user_email=user_email,
            user_role=user_role,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            details=details,
            ip_address=ip_address
        )
        db.add(log_entry)
        db.commit()
        return log_entry
    except Exception as e:
        print(f"Error writing audit log: {e}")
        db.rollback()
        return None
