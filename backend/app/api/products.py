"""
Legal Lens - Product Catalog API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Product, Inspection
from ..schemas import ProductOut

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("", response_model=List[ProductOut])
def list_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if category and category != "All":
        query = query.filter(Product.category == category)
    if search:
        s = f"%{search}%"
        query = query.filter((Product.product_name.ilike(s)) | (Product.brand.ilike(s)) | (Product.barcode.ilike(s)))
    return query.all()

@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/{product_id}/inspections")
def get_product_inspections(product_id: int, db: Session = Depends(get_db)):
    inspections = db.query(Inspection).filter(Inspection.product_id == product_id).order_by(Inspection.created_at.desc()).all()
    return [
        {
            "id": ins.id,
            "inspection_code": ins.inspection_code,
            "date": ins.created_at.strftime("%d %b %Y"),
            "status": ins.status,
            "overall_result": ins.overall_result,
            "rules_checked": ins.rules_checked_count,
            "non_compliance_count": ins.non_compliance_count,
            "officer_review_status": ins.officer_review_status
        }
        for ins in inspections
    ]
