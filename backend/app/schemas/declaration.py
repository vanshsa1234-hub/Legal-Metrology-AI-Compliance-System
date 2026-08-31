"""
Legal Lens - Extracted Declaration Schemas
"""
from typing import Optional
from pydantic import BaseModel


class ExtractedDeclarationOut(BaseModel):
    id: Optional[int] = None
    field_name: str
    detected_value: Optional[str] = None
    confidence: float
    confidence_level: str
    evidence_image_type: str
    bounding_box: Optional[str] = None
    is_verified: bool = False

    class Config:
        from_attributes = True
