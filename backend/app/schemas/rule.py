"""
Legal Lens - Legal Rule Schemas
"""
from typing import Optional
from pydantic import BaseModel


class LegalRuleOut(BaseModel):
    id: int
    rule_id: str
    rule_title: str
    legal_requirement: str
    description: str
    product_category: str
    mandatory_conditional: str
    evidence_required: Optional[str] = None
    applicable_regulation: str
    clause: Optional[str] = None
    version_amendment: Optional[str] = None
    effective_date: Optional[str] = None
    remarks: Optional[str] = None

    class Config:
        from_attributes = True
