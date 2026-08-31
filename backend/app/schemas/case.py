"""
Legal Lens - Case (Citizen Request) Schemas
"""
import datetime
from typing import List, Optional
from pydantic import BaseModel


class RequestCreate(BaseModel):
    inspection_id: Optional[int] = None
    product_name: str
    brand: Optional[str] = None
    barcode: Optional[str] = None
    mrp: Optional[str] = None
    category: Optional[str] = "Packaged Food"
    purchase_date: Optional[str] = None
    place_of_purchase: Optional[str] = None
    shop_name: str
    shop_address: str
    city: str
    state: Optional[str] = "Uttarakhand"
    market_area: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    citizen_name: str
    citizen_phone: str
    citizen_email: Optional[str] = None
    preferred_contact: Optional[str] = "Phone"
    description: str
    priority: Optional[str] = "High"


class OfficerActionCreate(BaseModel):
    new_status: str
    remarks: str


class OfficerActionOut(BaseModel):
    id: int
    officer_name: str
    action_type: str
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    remarks: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class RequestOut(BaseModel):
    id: int
    request_code: str
    inspection_id: Optional[int] = None
    user_id: Optional[int] = None
    product_name: str
    brand: Optional[str] = None
    barcode: Optional[str] = None
    mrp: Optional[str] = None
    category: Optional[str] = None
    purchase_date: Optional[str] = None
    place_of_purchase: Optional[str] = None
    shop_name: str
    shop_address: str
    city: str
    state: str
    market_area: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    citizen_name: str
    citizen_phone: str
    citizen_email: Optional[str] = None
    preferred_contact: str
    description: str
    priority: str
    status: str
    officer_remarks: Optional[str] = None
    officer_id: Optional[int] = None
    shop_image_path: Optional[str] = None
    bill_image_path: Optional[str] = None
    additional_evidence_path: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    officer_actions: List[OfficerActionOut] = []

    class Config:
        from_attributes = True
