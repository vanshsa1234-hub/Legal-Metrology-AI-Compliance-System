from ..database import SessionLocal
from ..services.inspection_processing import run_inspection_processing
from .celery_app import celery_app


@celery_app.task(name="process_inspection")
def process_inspection_task(inspection_id: int, barcode: str = None):
    """Runs OCR + rule evaluation for one inspection in a worker process."""
    db = SessionLocal()
    try:
        inspection = run_inspection_processing(db, inspection_id, barcode)
        return inspection.id
    finally:
        db.close()
