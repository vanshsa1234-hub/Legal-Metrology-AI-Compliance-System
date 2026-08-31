"""
Legal Lens - Legal Rule Model
Versioned statutory compliance rules, loaded from
rules/legal_rules/SIH_Legal_Compliance_Master.csv at startup.
"""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from ..database import Base


class LegalRule(Base):
    __tablename__ = "legal_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String(50), unique=True, index=True, nullable=False)
    rule_title = Column(String(200), nullable=False)
    legal_requirement = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    product_category = Column(String(100), nullable=False)
    mandatory_conditional = Column(String(50), default="Mandatory")
    evidence_required = Column(String(100), nullable=True)
    applicable_regulation = Column(String(250), nullable=False)
    clause = Column(String(100), nullable=True)
    version_amendment = Column(String(50), nullable=True)
    effective_date = Column(String(50), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
