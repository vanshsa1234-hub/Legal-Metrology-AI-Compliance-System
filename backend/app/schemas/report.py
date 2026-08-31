"""
Legal Lens - Report Schemas
"""
import datetime
from typing import Optional
from pydantic import BaseModel


class ReportOut(BaseModel):
    id: int
    report_code: str
    inspection_id: int
    file_path: str
    file_name: str
    summary: Optional[str] = None
    created_at: datetime.datetime
    product_name: Optional[str] = None
    overall_result: Optional[str] = None

    class Config:
        from_attributes = True
