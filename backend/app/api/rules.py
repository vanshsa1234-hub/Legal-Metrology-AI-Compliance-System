"""
Legal Lens - Compliance Rule Repository API
Backed strictly by SIH_Legal_Compliance_Master.csv
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import LegalRule
from ..schemas import LegalRuleOut

router = APIRouter(prefix="/api/rules", tags=["Rules"])

@router.get("", response_model=List[LegalRuleOut])
def list_rules(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(LegalRule)
    if category and category != "All":
        query = query.filter(LegalRule.product_category.ilike(f"%{category}%"))
    if search:
        s = f"%{search}%"
        query = query.filter(
            (LegalRule.rule_id.ilike(s)) |
            (LegalRule.rule_title.ilike(s)) |
            (LegalRule.description.ilike(s)) |
            (LegalRule.applicable_regulation.ilike(s))
        )
    return query.order_by(LegalRule.id.asc()).all()

@router.get("/categories")
def list_rule_categories(db: Session = Depends(get_db)):
    rules = db.query(LegalRule).all()
    categories = sorted(list(set(r.product_category for r in rules if r.product_category)))
    return categories

@router.get("/{rule_id}", response_model=LegalRuleOut)
def get_rule_detail(rule_id: str, db: Session = Depends(get_db)):
    rule = db.query(LegalRule).filter((LegalRule.rule_id == rule_id) | (LegalRule.id == rule_id)).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found in repository")
    return rule
