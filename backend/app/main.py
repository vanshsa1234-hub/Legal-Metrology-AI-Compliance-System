"""
Legal Lens - Main FastAPI Application
AI-Assisted Consumer Compliance & Product Inspection System
Smart India Hackathon Prototype (Problem Statement 26034)
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import engine, Base, SessionLocal
from .core.config import STORAGE_DIR, IMAGES_DIR, EVIDENCE_DIR, REPORTS_DIR, FRONTEND_DIR, APP_NAME, APP_VERSION, APP_DESCRIPTION
from .services.seed_data import seed_database
from .api import (
    auth, analytics, inspections, images, ocr, declarations, compliance,
    evidence, violations, cases, products, rules, reports, audit
)

# Initialize database schema (models/__init__.py has already imported
# every mapped class, so Base.metadata is fully populated here)
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
app.include_router(auth.router)
app.include_router(analytics.router)
app.include_router(inspections.router)
app.include_router(images.router)
app.include_router(ocr.router)
app.include_router(ocr.preview_router)
app.include_router(declarations.router)
app.include_router(compliance.router)
app.include_router(evidence.router)
app.include_router(violations.router)
app.include_router(cases.router)
app.include_router(products.router)
app.include_router(rules.router)
app.include_router(reports.router)
app.include_router(audit.router)

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
