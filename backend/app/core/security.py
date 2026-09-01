"""
Legal Lens - Security Utilities

Phase 1 (see docs/PRODUCTION_READINESS_PRD.md):
  - Passwords are salted + hashed with bcrypt via passlib.
  - Session tokens are signed, verifiable JWTs (python-jose), carrying
    the user id and role, with an expiry.
  - Verification lives in core/deps.py as a FastAPI dependency
    (get_current_user / require_roles) enforced on protected routers
    in main.py.

Existing rows created before this change (SHA-256 hex digests) will no
longer verify against bcrypt - re-seed the database
(delete backend/legallens.db and restart) after upgrading.
"""
import datetime
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Salted bcrypt hash of a plaintext password."""
    return _pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    try:
        return _pwd_context.verify(plain_password, password_hash)
    except (ValueError, TypeError):
        # Raised by passlib when password_hash isn't a bcrypt hash at
        # all (e.g. a leftover SHA-256 digest from before this change).
        return False


def create_access_token(user_id: int, role: str, expires_minutes: Optional[int] = None) -> str:
    """Issue a signed JWT carrying the user id and role."""
    expire_minutes = expires_minutes if expires_minutes is not None else JWT_EXPIRE_MINUTES
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=expire_minutes)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT. Raises jose.JWTError on failure/expiry."""
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
