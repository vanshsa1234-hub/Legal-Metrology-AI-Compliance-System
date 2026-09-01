# Legal Lens (MetrAI) — Production Readiness PRD

Source of truth for remaining gaps: `docs/ROADMAP.md` (verified against
actual code on 2026-08-31). This document sequences that work into
buildable phases. Each phase is independently shippable and testable.

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
- Enable `pgvector` extension on Postgres (depends on Phase 5).
- Embed `rules/legal_rules/` + amendments into a vector table.
- Add a retrieval endpoint + LLM-assisted ambiguity resolution for
  edge cases the deterministic rule engine can't classify.
- Out of scope until Phases 1–6 are stable; flagged here so it's not
  lost.

---

## Out of scope / explicitly deferred
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
