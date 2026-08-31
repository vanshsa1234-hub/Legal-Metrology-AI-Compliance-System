"""
Legal Lens - Pydantic Schemas
Single import surface for all request/response models used by the API.
"""
from .user import LoginRequest, UserOut, LoginResponse
from .rule import LegalRuleOut
from .declaration import ExtractedDeclarationOut
from .compliance import ComplianceResultOut
from .violation import ViolationOut
from .evidence import InspectionImageOut
from .inspection import InspectionCreate, InspectionOut
from .case import RequestCreate, RequestOut, OfficerActionCreate, OfficerActionOut
from .product import ProductOut
from .audit_log import AuditLogOut
from .report import ReportOut

__all__ = [
    "LoginRequest", "UserOut", "LoginResponse",
    "LegalRuleOut",
    "ExtractedDeclarationOut",
    "ComplianceResultOut", "ViolationOut",
    "InspectionImageOut",
    "InspectionCreate", "InspectionOut",
    "RequestCreate", "RequestOut", "OfficerActionCreate", "OfficerActionOut",
    "ProductOut",
    "AuditLogOut",
    "ReportOut",
]
