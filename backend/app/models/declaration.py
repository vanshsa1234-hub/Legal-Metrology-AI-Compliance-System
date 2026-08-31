"""
Legal Lens - Extracted Declaration Model
One mandatory-declaration field (MRP, net quantity, manufacturer, etc.)
extracted from a label, with its confidence score and evidence source.
"""
import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class ExtractedDeclaration(Base):
    __tablename__ = "extracted_declarations"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    detected_value = Column(Text, nullable=True)
    confidence = Column(Float, default=90.0)
    confidence_level = Column(String(20), default="High")
    evidence_image_type = Column(String(50), default="front")
    bounding_box = Column(String(100), nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    inspection = relationship("Inspection", back_populates="declarations")
