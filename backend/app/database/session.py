"""
Legal Lens - Database Engine & Session Management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..core.config import DATABASE_URL

# check_same_thread=False is a SQLite-only flag (it lets the connection
# be reused across FastAPI's threadpool); Postgres doesn't have or need it.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
