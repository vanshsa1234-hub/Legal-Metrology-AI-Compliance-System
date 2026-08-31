# backend/app/workers/ — Not yet implemented

Reserved for Celery task definitions once OCR/AI processing is moved
off the request/response cycle (see docs/MetraAI_Final_Tech_Stack.pdf
section 14). Today, `POST /api/inspections/{id}/process` runs
synchronously inside the request in
backend/app/api/inspections.py - fine for demo/pilot volume, but
worth moving to a background job before real enforcement-scale usage.
See docs/ROADMAP.md.
