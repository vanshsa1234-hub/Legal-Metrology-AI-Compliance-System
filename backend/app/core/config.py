"""
Legal Lens - Application Configuration

Centralizes all filesystem paths and app-level settings so the rest of
the codebase never hardcodes a path. All paths are computed relative to
this file's location, so the project can be cloned/moved anywhere.
"""
import os

# backend/app/core/config.py -> backend/app/core -> backend/app -> backend
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# backend/ -> project root
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

# --- Database ---
DB_PATH = os.path.join(BACKEND_DIR, "legallens.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# --- Shared storage (matches the top-level storage/ directory) ---
STORAGE_DIR = os.path.join(PROJECT_ROOT, "storage")
IMAGES_DIR = os.path.join(STORAGE_DIR, "images")
EVIDENCE_DIR = os.path.join(STORAGE_DIR, "evidence")
REPORTS_DIR = os.path.join(STORAGE_DIR, "reports")

# --- Legal rules source of truth ---
LEGAL_RULES_DIR = os.path.join(PROJECT_ROOT, "rules", "legal_rules")
LEGAL_RULES_CSV = os.path.join(LEGAL_RULES_DIR, "SIH_Legal_Compliance_Master.csv")

# --- Frontend (served statically by FastAPI) ---
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

# --- App metadata ---
APP_NAME = "Legal Lens"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "AI-Assisted Consumer Compliance & Packaged Product Inspection Platform"
