"""
Legal Lens - Product Schemas
"""
import datetime
from typing import Optional
from pydantic import BaseModel


class ProductOut(BaseModel):
    id: int
    product_name: str
    brand: str
    category: str
    sub_category: Optional[str] = None
    manufacturer: Optional[str] = None
    net_quantity: Optional[str] = None
    mrp: Optional[str] = None
    batch_number: Optional[str] = None
    mfg_date: Optional[str] = None
    best_before: Optional[str] = None
    consumer_care: Optional[str] = None
    ingredients: Optional[str] = None
    veg_non_veg: Optional[str] = None
    country_of_origin: Optional[str] = None
    barcode: Optional[str] = None
    fssai_license: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True
