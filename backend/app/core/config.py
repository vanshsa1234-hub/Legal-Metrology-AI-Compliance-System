"""
Legal Lens - Application Configuration

Centralizes all filesystem paths and app-level settings so the rest of
the codebase never hardcodes a path. All paths are computed relative to
this file's location, so the project can be cloned/moved anywhere.
"""
import os
import warnings

# backend/app/core/config.py -> backend/app/core -> backend/app -> backend
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# backend/ -> project root
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

# --- Database ---
# DATABASE_URL unset (local/dev/tests): SQLite file, zero setup needed.
# DATABASE_URL set (docker-compose's postgres service, Phase 5): Postgres.
DB_PATH = os.path.join(BACKEND_DIR, "legallens.db")
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

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

# --- Auth (Phase 1: docs/PRODUCTION_READINESS_PRD.md) ---
# JWT_SECRET_KEY must be set via env in any non-local deployment. The
# fallback below is only for local/dev convenience and is intentionally
# obvious so it's never mistaken for a real secret.
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-only-insecure-secret-change-me")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "60"))

if JWT_SECRET_KEY == "dev-only-insecure-secret-change-me":
    warnings.warn(
        "JWT_SECRET_KEY is not set - using an insecure development "
        "default. Set JWT_SECRET_KEY in the environment before "
        "deploying anywhere beyond a local demo.",
        RuntimeWarning,
    )
