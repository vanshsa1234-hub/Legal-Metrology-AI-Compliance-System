"""
Legal Lens - Evidence (Inspection Image) Schemas
"""
from pydantic import BaseModel


class InspectionImageOut(BaseModel):
    id: int
    image_type: str
    file_path: str
    file_name: str
    quality_score: float
    quality_label: str

    class Config:
        from_attributes = True
