"""
Legal Lens - Domain Models

This is the single import surface for all mapped SQLAlchemy classes.
Importing every submodule here (rather than relying on call sites to
import them individually) guarantees Base.metadata is fully populated
before main.py calls Base.metadata.create_all(), and before any
relationship() string reference is resolved.
"""
from .user import User
from .rule import LegalRule
from .product import Product
from .inspection import Inspection
from .evidence import InspectionImage
from .declaration import ExtractedDeclaration
from .compliance import ComplianceResult, STATUS_NO_ISSUE, STATUS_REVIEW_REQUIRED, STATUS_NON_COMPLIANCE
from .violation import Violation, get_violations
from .report import Report
from .case import Request, OfficerAction
from .audit_log import AuditLog

__all__ = [
    "User", "LegalRule", "Product", "Inspection", "InspectionImage",
    "ExtractedDeclaration", "ComplianceResult", "STATUS_NO_ISSUE",
    "STATUS_REVIEW_REQUIRED", "STATUS_NON_COMPLIANCE", "Violation",
    "get_violations", "Report", "Request", "OfficerAction", "AuditLog",
]
