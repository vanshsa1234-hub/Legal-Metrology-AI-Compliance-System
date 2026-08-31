"""
Legal Lens - Product Model
The structured product record built from OCR/label extraction.
"""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from ..database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(200), index=True, nullable=False)
    brand = Column(String(100), nullable=False)
    category = Column(String(100), default="Packaged Food")
    sub_category = Column(String(100), default="Snacks / Chips")
    manufacturer = Column(String(200), nullable=True)
    net_quantity = Column(String(50), nullable=True)
    mrp = Column(String(50), nullable=True)
    batch_number = Column(String(100), nullable=True)
    mfg_date = Column(String(50), nullable=True)
    best_before = Column(String(50), nullable=True)
    consumer_care = Column(String(150), nullable=True)
    ingredients = Column(Text, nullable=True)
    veg_non_veg = Column(String(50), default="Vegetarian")
    country_of_origin = Column(String(100), default="India")
    barcode = Column(String(100), index=True, nullable=True)
    fssai_license = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    inspections = relationship("Inspection", back_populates="product")
