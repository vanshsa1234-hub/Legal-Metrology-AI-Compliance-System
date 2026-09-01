"""
Legal Lens - Authentication API Routes

Issues signed JWTs on login (backend/app/core/security.py) and
verifies them via the get_current_user dependency
(backend/app/core/deps.py), enforced on every other router in main.py.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import LoginRequest, LoginResponse, UserOut
from ..services.audit_service import log_event
from ..core.security import verify_password, create_access_token
from ..core.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user or officer and issue a signed JWT."""
    email_clean = creds.email.strip().lower()

    user = db.query(User).filter(User.email == email_clean).first()
    if not user or not verify_password(creds.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    # Optional role check if passed from UI
    if creds.role and creds.role != user.role:
        if creds.role in ["officer", "admin"] and user.role not in ["officer", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: User does not have Officer/Admin privileges"
            )

    token = create_access_token(user_id=user.id, role=user.role)

    log_event(
        db=db,
        user_email=user.email,
        user_role=user.role,
        action="User Login",
        entity_type="Auth",
        details=f"Successful login for role: {user.role}"
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    """Get profile of the authenticated user (derived from the JWT)."""
    return current_user
