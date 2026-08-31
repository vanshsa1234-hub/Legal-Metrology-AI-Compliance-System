"""
Legal Lens - Compliance Result Model
One rule evaluation outcome for an inspection: NO ISSUE DETECTED,
REVIEW REQUIRED, or POTENTIAL NON-COMPLIANCE, with the deterministic
reasoning the rule engine produced.
"""
import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class ComplianceResult(Base):
    __tablename__ = "compliance_results"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    rule_id = Column(String(50), nullable=False)
    rule_title = Column(String(200), nullable=False)
    status = Column(String(50), nullable=False)
    confidence = Column(Float, default=85.0)
    evidence_type = Column(String(50), default="Back Image")
    reason = Column(Text, nullable=False)
    what_checked = Column(Text, nullable=False)
    what_found = Column(Text, nullable=False)
    why_flagged = Column(Text, nullable=True)
    applicable_regulation = Column(String(250), nullable=False)
    clause = Column(String(100), nullable=True)
    version_amendment = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    inspection = relationship("Inspection", back_populates="compliance_results")


# Status constants used across the rule engine, API layer, and frontend.
STATUS_NO_ISSUE = "NO ISSUE DETECTED"
STATUS_REVIEW_REQUIRED = "REVIEW REQUIRED"
STATUS_NON_COMPLIANCE = "POTENTIAL NON-COMPLIANCE"
