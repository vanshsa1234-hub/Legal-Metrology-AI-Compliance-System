"""
Legal Lens - Report Model
Metadata for a generated PDF compliance report; the file itself lives
under storage/reports/.
"""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    report_code = Column(String(50), unique=True, index=True, nullable=False)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    file_path = Column(String(300), nullable=False)
    file_name = Column(String(150), nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    inspection = relationship("Inspection", back_populates="reports")
