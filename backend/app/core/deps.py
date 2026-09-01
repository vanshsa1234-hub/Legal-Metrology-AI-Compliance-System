"""
Legal Lens - Auth Dependencies

FastAPI dependencies that verify the JWT on protected routes and
enforce role-based access. See docs/PRODUCTION_READINESS_PRD.md Phase 1.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from .security import decode_access_token

# auto_error=False so we can return a clean 401 (with a WWW-Authenticate
# header) instead of FastAPI's default 403 when the header is missing.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve and return the authenticated User for the request's JWT."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or not credentials.credentials:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise unauthorized

    user_id = payload.get("sub")
    if user_id is None:
        raise unauthorized

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise unauthorized
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    return user


def require_roles(*allowed_roles: str):
    """
    Dependency factory: builds a dependency that requires the current
    user's role to be one of allowed_roles.

    Usage: dependencies=[Depends(require_roles("officer", "admin"))]
    """
    def _guard(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {' or '.join(allowed_roles)}",
            )
        return current_user

    return _guard
