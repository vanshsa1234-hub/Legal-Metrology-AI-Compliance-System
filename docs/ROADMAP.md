# Roadmap / Known Limitations

This is the single source of truth for what's real and what's still
planned in Legal Lens (MetraAI). Every "not yet implemented" README
scattered around the repo points back here. Being upfront about this
list is intentional - SIH judges (and future contributors) trust a
team more when the gap between demo and production is documented,
not discovered live.

## Genuinely working today

- FastAPI backend with a full domain model (users, products,
  inspections, evidence, declarations, compliance results, cases,
  reports, audit log)
- A real, deterministic rule engine (`backend/app/services/rule_engine.py`)
  evaluating live against all 26 rules in
  `rules/legal_rules/SIH_Legal_Compliance_Master.csv`
- Real PDF compliance report generation (ReportLab)
- Real audit logging to the database
- A full citizen-complaint / officer-action workflow
- A working end-to-end frontend SPA wired to every one of the above
- An automated backend test suite (`tests/backend/test_api.py`)

## Simulated / demo-grade (top priority to replace)

1. **OCR / label extraction** (`backend/app/services/ocr_service.py`)
   Currently a hardcoded catalog of 3 demo barcodes; does not analyze
   uploaded images. Planned: PaddleOCR + OpenCV + YOLO +
   spaCy/Transformers, per `docs/MetraAI_Final_Tech_Stack.pdf`.
2. **Image quality checks** - only checks pixel dimensions today, not
   real blur/glare/contrast detection.
3. **Authentication** (`backend/app/core/security.py`) - unsalted
   SHA-256 password hashing, unsigned session tokens, and **no route
   currently verifies the token** - every API endpoint is effectively
   open. Planned: passlib (bcrypt/argon2) + python-jose JWTs +
   enforced RBAC.
4. **Weekly inspection trend chart** (`backend/app/api/analytics.py`)
   uses placeholder numbers, not a real `GROUP BY` query over
   inspection timestamps.

## Not yet started

- Background job processing (Celery + Redis) - `/process` currently
  runs synchronously in the request. See `backend/app/workers/README.md`.
- Object storage (MinIO/S3) - local disk under `storage/` is used today.
- PostgreSQL + pgvector - SQLite is used today; no vector search / Legal
  RAG exists yet.
- LLM-assisted ambiguity resolution.
- Database migrations (Alembic) - schema is created fresh via
  `Base.metadata.create_all()` on every startup.
- Rule versioning / amendment history (`rules/rule_versions/`,
  `rules/amendments/`).
- Richer rule applicability (pack type, sales channel, inspection
  date) beyond category/sub-category matching.
- Playwright end-to-end tests (`tests/e2e/`).

## Suggested build order

1. Real JWT auth + route protection (highest risk if left as-is)
2. Real OCR/CV pipeline (highest-value replacement for the demo catalog)
3. Background processing (Celery/Redis) once OCR is slow enough to need it
4. PostgreSQL migration + Alembic
5. Object storage (S3-compatible) once deploying beyond a single machine
