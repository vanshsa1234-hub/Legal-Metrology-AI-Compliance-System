"""
Legal Lens - Violation Schemas

A Violation is serialized identically to a ComplianceResult (see
models/violation.py for why there is no separate table). This alias
keeps the API response model named appropriately for /api/violations.
"""
from .compliance import ComplianceResultOut as ViolationOut

__all__ = ["ViolationOut"]
