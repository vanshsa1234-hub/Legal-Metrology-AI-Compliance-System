"""
Legal Lens - Inspection Model
The central record tying together images, extracted declarations,
compliance results, and the generated report for one scan session.
"""
import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    inspection_code = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(200), nullable=True)
    brand = Column(String(100), nullable=True)
    category = Column(String(100), default="Packaged Food")
    barcode = Column(String(100), nullable=True)

    status = Column(String(50), default="Processing", nullable=False)
    overall_result = Column(String(50), default="Review Required")
    confidence_score = Column(Float, default=0.0)

    rules_checked_count = Column(Integer, default=0)
    no_issue_count = Column(Integer, default=0)
    review_required_count = Column(Integer, default=0)
    non_compliance_count = Column(Integer, default=0)

    officer_review_status = Column(String(50), default="Pending")
    officer_remarks = Column(Text, nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id], back_populates="inspections")
    product = relationship("Product", back_populates="inspections")
    images = relationship("InspectionImage", back_populates="inspection", cascade="all, delete-orphan")
    declarations = relationship("ExtractedDeclaration", back_populates="inspection", cascade="all, delete-orphan")
    compliance_results = relationship("ComplianceResult", back_populates="inspection", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="inspection", cascade="all, delete-orphan")
    requests = relationship("Request", back_populates="inspection")
