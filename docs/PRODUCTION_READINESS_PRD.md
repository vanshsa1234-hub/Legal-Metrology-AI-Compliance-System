# Legal Lens (MetrAI) — Production Readiness PRD

Source of truth for remaining gaps: `docs/ROADMAP.md` (verified against
actual code on 2026-08-31). This document sequences that work into
buildable phases. Each phase is independently shippable and testable.

**Status: all 12 phases below are complete, 28/28 backend tests
passing.** This document is kept as the historical plan; for what each
phase actually delivered (including honest caveats like PaddleOCR's
weight download being unverified in the build/test sandbox, and YOLO
only covering COCO's bottle/cup/bowl classes), see the "Genuinely
working today" section of `docs/ROADMAP.md` — it's the more current,
outcome-focused document of the two.

Confirmed already done (not in scope below): real OCR (Tesseract +
OpenCV), real image quality scoring, real rule engine, real PDF
reports, real audit logging.

---

## Phase 1 — Real Authentication + RBAC Enforcement
**Why first:** every API endpoint is currently unauthenticated. Highest
risk item, blocks everything else being "production" in any sense.

- Replace `hash_password` (unsalted SHA-256) with passlib bcrypt.
- Replace `generate_session_token` with signed JWTs (python-jose),
  including expiry (`JWT_EXPIRE_MINUTES`).
- Add `get_current_user()` FastAPI dependency that verifies the
  `Authorization: Bearer` header.
- Enforce the dependency on every protected router (all routers except
  `/api/auth/login`, `/api/health`, static mounts).
- Add role-based guards (e.g. `require_role("officer")`) on
  officer/admin-only endpoints (rules, reports, audit, case actions).
- Migrate `backend/.env.example` values (`JWT_SECRET_KEY`, etc.) into
  actually-read settings in `core/config.py`.
- Update frontend `app.js` to store/send the JWT and handle 401s
  (redirect to login).
- Tests: login issues a real JWT; protected route rejects missing/
  expired/tampered token; role guard rejects wrong role.

## Phase 2 — Real Analytics (kill hardcoded chart data)
**Why second:** small, self-contained, high visible impact, no
dependency on Phase 1.

- `backend/app/api/analytics.py`: replace the hardcoded weekly trend
  array with a real `GROUP BY date` query over `Inspection.created_at`
  for the last 7 days (zero-fill missing days).
- Replace hardcoded category-distribution fallback with a real query;
  only show a documented "no data yet" empty state when the table is
  genuinely empty (no fabricated numbers).
- Tests: seed N inspections across dates, assert chart data matches.

## Phase 3 — Wire the Frontend Pipeline Animation to Real Progress
- Replace the fixed-delay `setTimeout` step list in `app.js` with
  either (a) polling a real `/process/{job_id}/status` endpoint, or
  (b) sequencing the steps around the actual awaited API calls so
  labels reflect real request/response boundaries, not fake timers.
- Depends on Phase 4 if we want true async progress (job status);
  otherwise a lighter sync version ships now and gets upgraded later.

## Phase 4 — Background Processing (Celery + Redis)
**Why fourth:** OCR/CV is real work now (Phase 1's roadmap point 1),
so synchronous request handling is a real bottleneck, not a cosmetic
gap anymore.

- Add Celery app + Redis broker config (`backend/app/workers/`).
- Move `/process` (OCR + rule engine run) into a Celery task.
- Add job status table/endpoint for the frontend to poll.
- Docker Compose: add `redis` and `worker` services.
- Tests: task enqueues, worker (eager mode in tests) produces same
  result as the old synchronous path.

## Phase 5 — PostgreSQL Migration + Alembic
- Swap SQLite → PostgreSQL in `core/config.py` / `DATABASE_URL`.
- Generate initial Alembic migration from current models (replacing
  `Base.metadata.create_all()` on startup).
- Docker Compose: add `postgres` service.
- Update `docker/Dockerfile.backend` and README setup steps.

## Phase 6 — Object Storage (S3/MinIO)
- Add MinIO service to Docker Compose (local S3-compatible dev target).
- Add a storage abstraction (`StorageBackend`) with local-disk and
  S3 implementations; switch via env var so local dev still works
  without MinIO running.
- Migrate image/evidence/report upload+read paths to the abstraction.

## Phase 7 — Legal RAG / pgvector / LLM (stretch)

**Status: done.** Delivered as retrieval-first, LLM-optional:

- `POST /api/rag/resolve` retrieves the legal rules most relevant to a
  free-text compliance question via TF-IDF cosine similarity, computed
  on the fly over the current rules table (`backend/app/services/rag_service.py`).
- If `ANTHROPIC_API_KEY` is set, that retrieved evidence grounds a
  short, rule-ID-cited answer via the Anthropic API. Without a key,
  the endpoint still returns the retrieved rules - it never fabricates
  an answer standing in for a real model call.
- pgvector is enabled on Postgres via a genuinely safe migration
  (a no-op on SQLite, confirmed with `alembic check`), available as a
  drop-in upgrade path.
- Deliberately *not* built: a persisted vector table or ANN index.
  At today's scale (~30 rules) an in-Python similarity computation is
  exact and sub-millisecond - that complexity wasn't earning its keep.
  Revisit if the rules corpus grows into the thousands.

---

**All 7 phases above are complete.** Phases 8–12 below close the
remaining gaps between the implementation and the target architecture
(Frontend → FastAPI → Postgres/Redis/Celery → OpenCV/PaddleOCR/YOLO/
NLP → Compliance Engine → RAG+Rules → Human Review → ReportLab →
MinIO), based on a side-by-side review against that diagram.

## Phase 8 — Full Stack as the Default Runtime Path
Phases 4–6 made Postgres/Redis/MinIO real but *optional* (env-gated,
falling back to SQLite/inline/local-disk when unset) - correct for
zero-setup local dev, but it means the diagram's stack isn't what
actually runs unless you remember to set env vars. This phase doesn't
remove the fallback (still needed for the test suite), it makes the
full stack the documented, one-command default:
- A `backend/.env` generated/documented to match `docker-compose.yml`
  exactly, so `docker compose up` *is* the default path, not a manual
  opt-in.
- README updated so "how do I run this" leads with `docker compose up`
  (full stack), with bare `uvicorn` (SQLite/inline/local-disk) called
  out as the lightweight fallback for local development only.

## Phase 9 — Pluggable OCR Engine (Tesseract default, PaddleOCR optional)
- Extract an `OCREngine` interface out of `ocr_service.py` so the
  text-recognition step is swappable without touching the regex
  parsers, quality scoring, or callers.
- `TesseractEngine` (current behavior, default, zero extra setup).
- `PaddleOCREngine` (used when `OCR_ENGINE=paddleocr` and the
  `paddleocr` package + model weights are available), matching the
  original tech-stack doc.
- Honest caveat: PaddleOCR's model weights are hosted on Baidu's
  `bcebos.com`, which isn't reachable from this sandbox's restricted
  network, so the weight-download path can't be verified end-to-end
  here the way Phase 10/11's GitHub-hosted weights can. The engine
  abstraction and fallback logic are still fully real and tested;
  only the actual PaddleOCR inference call is unverified in this
  environment specifically.

## Phase 10 — YOLO Product/Package Localization
- Add a pretrained YOLOv8 (COCO-class) detection pass before OCR to
  localize the physical product package in the photo and crop to it,
  cutting out background/table/hand clutter before Tesseract runs.
- Honest scope: this detects generic package/container classes
  (bottle, box, etc.) that pretrained YOLO already knows - it does
  **not** localize a "declaration panel" sub-region specifically,
  since that's a custom object class with no existing labeled
  training data. True declaration-panel detection would need a
  labeling effort (a few hundred annotated package photos) before a
  custom YOLO head could be trained - flagged as a follow-up, not
  attempted here without that data.
- Falls back to OCRing the full image (today's behavior) if YOLO
  finds no package region, so this can only improve extraction
  quality, never regress it.

## Phase 11 — NLP-Assisted Field Extraction
- Add spaCy (`en_core_web_sm`) as a second signal alongside the
  existing regex/positional heuristics for product_name/brand/
  manufacturer extraction - named-entity recognition (ORG, PRODUCT-like
  spans) cross-checked against the position-based guess, raising
  confidence when they agree and flagging for review when they don't,
  rather than replacing the regex extraction (which handles
  structured fields like MRP/dates/batch numbers that NER isn't suited
  for) outright.

## Phase 12 — Explicit "Final Evidence → Human Review" Stage
- The diagram shows a distinct merge step between RAG+Rules and Human
  Review, before ReportLab. Today that's implicit (a `ComplianceResult`
  set plus a separately-triggered citizen request). This phase adds an
  explicit `EvidenceBundle` assembly step that merges OCR output +
  rule-engine results + (if queried) RAG-retrieved supporting rules
  into one reviewable object *before* report generation, and surfaces
  it as a distinct "Pending Human Review" state for
  `Review Required`/`Potential Non-Compliance` inspections rather than
  relying on the citizen to separately file a request to get officer
  eyes on it.

- Real barcode/camera hardware scanning (manual entry remains
  acceptable for this product's workflow — inspectors key in barcodes
  they read off physical packaging).
- Rule versioning UI (`rules/rule_versions/`, `rules/amendments/`)
  beyond what the rule engine already reads.
- Playwright e2e suite — nice to have, not blocking.

## Working agreement
- We execute phases one at a time, in order, each ending in a
  runnable/testable state.
- Each phase updates `docs/ROADMAP.md` to move items from "Simulated"
  / "Not yet started" into "Genuinely working today" as they land.
- No phase touches the already-real OCR/rule-engine/report code
  unless a later phase explicitly requires it (e.g. Phase 4 wrapping
  it in a Celery task).
