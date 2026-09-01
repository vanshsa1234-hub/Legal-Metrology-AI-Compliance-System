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
- **Real OCR and image quality analysis** (`backend/app/services/ocr_service.py`):
  - Image quality scoring via OpenCV (blur via Laplacian variance,
    brightness, contrast, glare/overexposure) - reads actual pixels,
    not just file dimensions.
  - Text extraction via Tesseract (pytesseract), with image
    preprocessing (denoising, adaptive thresholding, upscaling).
  - Regex-based structured field extraction for MRP, net quantity,
    batch number, FSSAI license, mfg/best-before dates, manufacturer,
    ingredients, and consumer-care contact details, from the real
    recognized text.
  - Confidence scores are Tesseract's own per-word confidence values,
    aggregated per field - not invented numbers.
  - Veg/Non-Veg mark detection via colour-region analysis (green vs.
    brown/maroon square) on the front image.
  - The old hardcoded 3-barcode demo catalog has been removed
    entirely. If no images are uploaded, the extraction is
    intentionally sparse, and the rule engine correctly flags missing
    declarations as REVIEW REQUIRED - it no longer fabricates a
    passing result.
- Real PDF compliance report generation (ReportLab)
- Real audit logging to the database
- A full citizen-complaint / officer-action workflow
- A working end-to-end frontend SPA wired to every one of the above
- An automated backend test suite (`tests/backend/test_api.py`),
  including a test that builds a real synthetic label image and
  verifies OCR actually reads a value burned into its pixels
- **Real authentication + RBAC** (`backend/app/core/security.py`,
  `backend/app/core/deps.py`): salted bcrypt password hashing
  (passlib), signed/verifiable JWTs (python-jose) with expiry, a
  `get_current_user()` dependency enforced on every router except
  `/api/auth/login` and `/api/health`, and `require_roles()` guards on
  officer/admin-only endpoints (admin dashboard, officer case actions,
  audit trail). Endpoints that used to trust a client-supplied
  `user_id`/`officer_id` now derive it from the verified token. Covered
  by `tests/backend/test_api.py` (missing token, tampered token, wrong
  password, and RBAC-blocked-role cases). See
  `docs/PRODUCTION_READINESS_PRD.md` for the full phase plan this was
  Phase 1 of.
- **Real admin dashboard analytics** (`backend/app/api/analytics.py`):
  the weekly inspections-trend chart is a real `GROUP BY date(...)`
  query over `Inspection.created_at` for the last 7 days (zero-filled,
  not fabricated), and the category-breakdown chart is a real
  `GROUP BY` over `Product.category`. Both the old hardcoded
  `[12, 19, 15, 25, 22, 30, ...]` trend array and the hardcoded
  `["Packaged Food", "Packaged Water", "Probiotic Foods"] / [3, 1, 1]`
  category fallback have been removed - an empty result now returns a
  genuinely empty chart instead of invented numbers. Covered by
  `tests/backend/test_api.py`. This was Phase 2.
- **Real processing pipeline UI** (`frontend/js/app.js`,
  `startProcessingPipeline()`): removed the scripted `setTimeout` step
  list entirely. Every step shown is now sequenced around a real
  awaited backend call and reports what that call actually returned
  (e.g. the real OpenCV quality score/label per uploaded image, the
  real declaration/rule counts from `/process`). This also fixed a
  real bug it uncovered: the frontend was never calling
  `POST /api/inspections/{id}/images` at all, so captured package
  photos were held in browser memory but never sent to the backend -
  `/process` always ran with zero images and fell back to
  "Unidentified Product (no images supplied)" regardless of what the
  user photographed. The demo "simulate images" button also generated
  an empty placeholder `Blob` instead of real JPEG bytes, so even the
  demo path never gave OCR anything to read; it now produces real
  JPEG blobs via `canvas.toBlob()`. Granular sub-progress *during* the
  single OCR+rule-engine `/process` call (e.g. a live percentage while
  it's running) needs a backend job-status endpoint to poll - that's
  Phase 4 (Celery/Redis), not attempted here. This was Phase 3.

## Simulated / demo-grade (top priority to replace)

~~**Authentication**~~ - **done, see "Genuinely working today" above.**

1. **OCR engine choice** - uses Tesseract, not PaddleOCR + YOLO as
   named in the original tech stack doc. Tesseract is real, working,
   open-source OCR (not a shortcut), but it's less robust than
   PaddleOCR on stylised packaging fonts and non-Latin scripts, and
   there's no YOLO step to localize a "declaration panel" before
   OCRing - the whole image is scanned every time. Swapping the
   engine only requires editing `OCRService._run_ocr()`.
2. **Product name / brand / manufacturer extraction** uses
   position-based heuristics (largest text near the top = probable
   product name) rather than a trained NER model, and is explicitly
   scored with lower confidence for this reason. Real barcode-based
   product lookup (reusing a previously-seen `Product` row) is used
   when available, which is genuine, not invented.
3. ~~**Weekly inspection trend chart**~~ - **done, see "Genuinely working today" above.**
4. ~~**Frontend "processing pipeline" animation**~~ - **done, see "Genuinely working today" above.** Remaining limitation (by design, deferred to Phase 4): no granular live percentage *during* the single `/process` call itself, since the backend doesn't expose mid-request progress events without a job-status endpoint to poll.

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

See `docs/PRODUCTION_READINESS_PRD.md` for the full phased plan.

1. ~~Real JWT auth + route protection~~ - **done (Phase 1)**
2. ~~Real OCR/CV pipeline~~ - **done**
3. ~~Real analytics (kill hardcoded chart data)~~ - **done (Phase 2)**
4. ~~Wire frontend pipeline animation to real progress~~ - **done (Phase 3)**
5. Background processing (Celery/Redis) - **Phase 4, next**
6. PostgreSQL migration + Alembic (Phase 5)
7. Object storage (S3-compatible) (Phase 6)
8. Legal RAG / pgvector / LLM (Phase 7, stretch)
