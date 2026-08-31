"""
Legal Lens - Compliance Result Schemas
"""
from typing import Optional
from pydantic import BaseModel


class ComplianceResultOut(BaseModel):
    id: Optional[int] = None
    rule_id: str
    rule_title: str
    status: str
    confidence: float
    evidence_type: str
    reason: str
    what_checked: str
    what_found: str
    why_flagged: Optional[str] = None
    applicable_regulation: str
    clause: Optional[str] = None
    version_amendment: Optional[str] = None

    class Config:
        from_attributes = True
