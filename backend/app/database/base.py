"""
Legal Lens - SQLAlchemy Declarative Base

Kept in its own module (separate from session.py) so model files can
import Base without triggering engine/session creation.
"""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
