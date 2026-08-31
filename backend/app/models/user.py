"""
Legal Lens - User Model
Represents citizens, enforcement officers, and administrators.
"""
import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, index=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(20), default="user", nullable=False)  # 'user', 'officer', 'admin'
    designation = Column(String(100), default="Consumer / Citizen")
    department = Column(String(100), default="General Public")
    badge_number = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    inspections = relationship("Inspection", foreign_keys="[Inspection.user_id]", back_populates="user")
    requests = relationship("Request", foreign_keys="[Request.user_id]", back_populates="user")
