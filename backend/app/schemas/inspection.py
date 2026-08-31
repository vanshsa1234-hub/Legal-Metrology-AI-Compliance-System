"""
Legal Lens - Inspection Schemas
"""
import datetime
from typing import List, Optional
from pydantic import BaseModel

from .evidence import InspectionImageOut
from .declaration import ExtractedDeclarationOut
from .compliance import ComplianceResultOut


class InspectionCreate(BaseModel):
    barcode: Optional[str] = None
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = "Packaged Food"


class InspectionOut(BaseModel):
    id: int
    inspection_code: str
    user_id: Optional[int] = None
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = "Packaged Food"
    barcode: Optional[str] = None
    status: str
    overall_result: str
    confidence_score: float
    rules_checked_count: int
    no_issue_count: int
    review_required_count: int
    non_compliance_count: int
    officer_review_status: str
    officer_remarks: Optional[str] = None
    created_at: datetime.datetime
    images: List[InspectionImageOut] = []
    declarations: List[ExtractedDeclarationOut] = []
    compliance_results: List[ComplianceResultOut] = []

    class Config:
        from_attributes = True
