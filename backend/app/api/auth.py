"""
Legal Lens - Authentication API Routes

See core/security.py for the current auth limitations (demo-grade
hashing, unverified tokens) before relying on this for real users.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import LoginRequest, LoginResponse, UserOut
from ..services.audit_service import log_event
from ..core.security import hash_password, generate_session_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user or officer."""
    email_clean = creds.email.strip().lower()
    pw_hash = hash_password(creds.password)

    user = db.query(User).filter(User.email == email_clean).first()
    if not user or user.password_hash != pw_hash:
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

    token = generate_session_token(user.id, user.role)

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
def get_current_user(user_id: int = 1, db: Session = Depends(get_db)):
    """Get profile of the active user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
