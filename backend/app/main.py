"""
Legal Lens - Main FastAPI Application
AI-Assisted Consumer Compliance & Product Inspection System
Smart India Hackathon Prototype (Problem Statement 26034)
"""
import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import engine, Base, SessionLocal
from .core.config import STORAGE_DIR, IMAGES_DIR, EVIDENCE_DIR, REPORTS_DIR, FRONTEND_DIR, APP_NAME, APP_VERSION, APP_DESCRIPTION
from .core.deps import get_current_user
from .services.seed_data import seed_database
from .api import (
    auth, analytics, inspections, images, ocr, declarations, compliance,
    evidence, violations, cases, products, rules, reports, audit, rag
)

# Initialize database schema (models/__init__.py has already imported
# every mapped class, so Base.metadata is fully populated here).
#
# Phase 5 (docs/PRODUCTION_READINESS_PRD.md) added real Alembic
# migrations (backend/alembic/) as the source of truth for schema
# changes going forward. create_all() is left here too, deliberately:
# it's a no-op against a DB Alembic already migrated (SQLAlchemy only
# creates tables that don't exist yet), and it keeps `uvicorn app.main:app`
# working with zero setup for local dev/tests against SQLite. Run
# `alembic upgrade head` explicitly before starting the app in any
# environment where migrations (not create_all) should own the schema.
Base.metadata.create_all(bind=engine)

# Run seed routine on startup
db = SessionLocal()
try:
    seed_database(db)
finally:
    db.close()

app = FastAPI(
    title=f"{APP_NAME} API",
    description=APP_DESCRIPTION,
    version=APP_VERSION
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
# auth.router is intentionally public (POST /login must be reachable
# without a token; /me protects itself via its own Depends).
# Every other router requires a valid JWT (Phase 1 - see
# docs/PRODUCTION_READINESS_PRD.md). Stricter per-route role guards
# (require_roles(...)) are layered on top inside individual routers
# where an endpoint needs officer/admin only.
_auth_required = [Depends(get_current_user)]

app.include_router(auth.router)
app.include_router(analytics.router, dependencies=_auth_required)
app.include_router(inspections.router, dependencies=_auth_required)
app.include_router(images.router, dependencies=_auth_required)
app.include_router(ocr.router, dependencies=_auth_required)
app.include_router(ocr.preview_router, dependencies=_auth_required)
app.include_router(declarations.router, dependencies=_auth_required)
app.include_router(compliance.router, dependencies=_auth_required)
app.include_router(evidence.router, dependencies=_auth_required)
app.include_router(violations.router, dependencies=_auth_required)
app.include_router(cases.router, dependencies=_auth_required)
app.include_router(products.router, dependencies=_auth_required)
app.include_router(rules.router, dependencies=_auth_required)
app.include_router(reports.router, dependencies=_auth_required)
app.include_router(audit.router, dependencies=_auth_required)
app.include_router(rag.router, dependencies=_auth_required)

# Ensure storage directories exist
os.makedirs(os.path.join(IMAGES_DIR, "products"), exist_ok=True)
os.makedirs(os.path.join(IMAGES_DIR, "shops"), exist_ok=True)
os.makedirs(EVIDENCE_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Mount static asset endpoints
# /uploads/images/products/... and /uploads/evidence/... both resolve
# under storage/, matching the URLs api/images.py and api/cases.py hand
# back to the frontend.
app.mount("/uploads", StaticFiles(directory=STORAGE_DIR), name="uploads")
app.mount("/reports", StaticFiles(directory=REPORTS_DIR), name="reports")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": f"{APP_NAME} API is running. Frontend static file not found at expected path."}


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "system": APP_NAME,
        "environment": "SIH-Prototype",
        "compliance_rules": 26
    }
