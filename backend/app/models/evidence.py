"""
Legal Lens - Evidence Model
Captured product images (front/back label photos) attached to an
inspection, along with an image-quality assessment used to flag
poor-quality captures before extraction runs.
"""
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class InspectionImage(Base):
    __tablename__ = "inspection_images"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    image_type = Column(String(50), nullable=False)  # 'front', 'back', etc.
    file_path = Column(String(300), nullable=False)
    file_name = Column(String(150), nullable=False)
    quality_score = Column(Float, default=95.0)
    quality_label = Column(String(50), default="Good")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    inspection = relationship("Inspection", back_populates="images")
