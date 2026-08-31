"""
Legal Lens - Case Model
A citizen-raised compliance complaint ("Request") and the trail of
officer actions taken against it. Named `case.py` to match the
enforcement-case terminology used elsewhere in the platform, while
keeping the underlying table name (`requests`) unchanged for backward
compatibility with existing data.
"""
import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    request_code = Column(String(50), unique=True, index=True, nullable=False)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    product_name = Column(String(200), nullable=False)
    brand = Column(String(100), nullable=True)
    barcode = Column(String(100), nullable=True)
    mrp = Column(String(50), nullable=True)
    category = Column(String(100), default="Packaged Food")
    purchase_date = Column(String(50), nullable=True)
    place_of_purchase = Column(String(200), nullable=True)

    shop_name = Column(String(200), nullable=False)
    shop_address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), default="Uttarakhand")
    market_area = Column(String(150), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    citizen_name = Column(String(120), nullable=False)
    citizen_phone = Column(String(50), nullable=False)
    citizen_email = Column(String(120), nullable=True)
    preferred_contact = Column(String(50), default="Phone")
    description = Column(Text, nullable=False)

    shop_image_path = Column(String(300), nullable=True)
    bill_image_path = Column(String(300), nullable=True)
    additional_evidence_path = Column(String(300), nullable=True)

    priority = Column(String(20), default="High")
    status = Column(String(50), default="Submitted", nullable=False)

    officer_remarks = Column(Text, nullable=True)
    officer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action_taken_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id], back_populates="requests")
    inspection = relationship("Inspection", back_populates="requests")
    officer_actions = relationship("OfficerAction", back_populates="request", cascade="all, delete-orphan")


class OfficerAction(Base):
    __tablename__ = "officer_actions"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=True)
    officer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    officer_name = Column(String(120), nullable=False)
    action_type = Column(String(100), nullable=False)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    request = relationship("Request", back_populates="officer_actions")
