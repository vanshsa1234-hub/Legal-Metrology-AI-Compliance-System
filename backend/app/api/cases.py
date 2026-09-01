"""
Legal Lens - Case (Citizen Request) & Officer Action API

Named cases.py to match enforcement-case terminology used elsewhere,
but URL prefix is kept as /api/requests so the existing frontend calls
(POST /api/requests, GET /api/requests/{id}, etc.) keep working
unchanged.
"""
import os
import shutil
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..database import get_db
from ..core.config import EVIDENCE_DIR
from ..models import Request, OfficerAction, Inspection, User
from ..schemas import RequestOut, RequestCreate, OfficerActionCreate
from ..services.audit_service import log_event
from ..core.deps import get_current_user, require_roles

router = APIRouter(prefix="/api/requests", tags=["Cases"])


def generate_request_code(db: Session) -> str:
    count = db.query(Request).count() + 1
    return f"LL-REQ-2026-{count:04d}"


@router.post("", response_model=RequestOut)
def create_request(
    data: RequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Citizen raises a compliance request / complaint."""
    user_id = current_user.id
    code = generate_request_code(db)
    req = Request(
        request_code=code,
        inspection_id=data.inspection_id,
        user_id=user_id,
        product_name=data.product_name,
        brand=data.brand,
        barcode=data.barcode,
        mrp=data.mrp,
        category=data.category or "Packaged Food",
        purchase_date=data.purchase_date or datetime.datetime.utcnow().strftime("%d %b %Y"),
        place_of_purchase=data.place_of_purchase,
        shop_name=data.shop_name,
        shop_address=data.shop_address,
        city=data.city,
        state=data.state or "Uttarakhand",
        market_area=data.market_area,
        latitude=data.latitude,
        longitude=data.longitude,
        citizen_name=data.citizen_name,
        citizen_phone=data.citizen_phone,
        citizen_email=data.citizen_email,
        preferred_contact=data.preferred_contact or "Phone",
        description=data.description,
        priority=data.priority or "High",
        status="Submitted"
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    log_event(
        db=db,
        user_email=current_user.email,
        user_role=current_user.role,
        action="Request Raised",
        entity_type="Request",
        entity_id=code,
        details=f"Raised compliance complaint for product '{req.product_name}' at '{req.shop_name}' ({req.city})"
    )

    return req


@router.post("/{request_id}/evidence")
async def upload_request_evidence(
    request_id: int,
    evidence_type: str = Form(...),  # 'shop', 'bill', 'additional'
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload evidence photo for shop or purchase bill."""
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    os.makedirs(EVIDENCE_DIR, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1] or ".jpg"
    safe_filename = f"{req.request_code}_{evidence_type}_{int(datetime.datetime.utcnow().timestamp())}{file_ext}"
    file_path = os.path.join(EVIDENCE_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    rel_url = f"/uploads/evidence/{safe_filename}"
    if evidence_type == "shop":
        req.shop_image_path = rel_url
    elif evidence_type == "bill":
        req.bill_image_path = rel_url
    else:
        req.additional_evidence_path = rel_url

    db.commit()

    return {
        "status": "success",
        "evidence_type": evidence_type,
        "file_url": rel_url
    }


@router.get("", response_model=List[RequestOut])
def list_requests(
    user_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List raised requests with search & filters.
    Citizens ('user' role) only ever see their own requests, regardless
    of the user_id query param. Officers/admins may view any user's
    requests (or all, when user_id is omitted).
    """
    query = db.query(Request)
    if current_user.role == "user":
        query = query.filter(Request.user_id == current_user.id)
    elif user_id:
        query = query.filter(Request.user_id == user_id)
    if status_filter and status_filter != "All":
        query = query.filter(Request.status == status_filter)
    if priority_filter and priority_filter != "All":
        query = query.filter(Request.priority == priority_filter)
    if search:
        s = f"%{search}%"
        query = query.filter(
            (Request.product_name.ilike(s)) |
            (Request.shop_name.ilike(s)) |
            (Request.request_code.ilike(s)) |
            (Request.city.ilike(s))
        )

    return query.order_by(Request.created_at.desc()).all()


@router.get("/{request_id}", response_model=RequestOut)
def get_request(request_id: int, db: Session = Depends(get_db)):
    """Get full detail of a specific request."""
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


@router.post(
    "/{request_id}/action",
    response_model=RequestOut,
    dependencies=[Depends(require_roles("officer", "admin"))],
)
def record_officer_action(
    request_id: int,
    action_data: OfficerActionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Officer reviews request, records official remarks, and updates status."""
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    officer_id = current_user.id
    officer_name = current_user.full_name

    old_status = req.status
    req.status = action_data.new_status
    req.officer_remarks = action_data.remarks
    req.officer_id = officer_id
    req.action_taken_at = datetime.datetime.utcnow()

    if req.inspection_id:
        ins = db.query(Inspection).filter(Inspection.id == req.inspection_id).first()
        if ins:
            if action_data.new_status in ["Resolved", "Mark Verified"]:
                ins.officer_review_status = "Verified"
            elif action_data.new_status in ["Mark Non-Compliance Confirmed", "Action Initiated"]:
                ins.officer_review_status = "Non-Compliance Confirmed"
            elif action_data.new_status == "Under Review":
                ins.officer_review_status = "Pending"
            ins.officer_remarks = action_data.remarks

    action_entry = OfficerAction(
        request_id=req.id,
        inspection_id=req.inspection_id,
        officer_id=officer_id,
        officer_name=officer_name,
        action_type=f"Status changed to {action_data.new_status}",
        previous_status=old_status,
        new_status=action_data.new_status,
        remarks=action_data.remarks
    )
    db.add(action_entry)
    db.commit()

    log_event(
        db=db,
        user_email=current_user.email,
        user_role="officer",
        action="Officer Action Recorded",
        entity_type="Request",
        entity_id=req.request_code,
        details=f"Status: {old_status} -> {action_data.new_status}. Remarks: '{action_data.remarks}'"
    )

    db.refresh(req)
    return req
