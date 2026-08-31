"""
Legal Lens - Audit Log Schemas
"""
import datetime
from typing import Optional
from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    timestamp: datetime.datetime
    user_email: str
    user_role: str
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True
