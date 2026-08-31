"""
Legal Lens - Security Utilities

IMPORTANT (read before demoing to judges or handling real user data):
This module currently implements DEMO-GRADE auth only:
  - Passwords are hashed with unsalted SHA-256 (hash_password).
  - "Tokens" are opaque, unsigned strings (generate_session_token) and are
    NOT verified on any protected route today - every API endpoint is
    effectively open right now.

Before production use, replace this with:
  - Salted password hashing via passlib (bcrypt or argon2).
  - Signed, verifiable JWTs via python-jose, with a get_current_user()
    dependency enforced on every protected router.
  - Role-based access control (RBAC) checks per route/action.

See docs/ROADMAP.md for the tracked list of what still needs to be built.
"""
import hashlib


def hash_password(password: str) -> str:
    """Demo-grade password hashing. NOT suitable for production."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def generate_session_token(user_id: int, role: str) -> str:
    """
    Generates an opaque session identifier for the demo prototype.
    This is NOT a verifiable JWT and is not currently checked by any
    route. Replace with a signed JWT before handling real credentials.
    """
    return f"legallens-token-{user_id}-{role}"
