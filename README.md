# Legal Lens (MetraAI)

**AI-Assisted Consumer Compliance & Packaged Product Inspection Platform**
Smart India Hackathon 2026 — Problem Statement 26034
*Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011.*

Legal Lens helps enforcement officials and citizens check packaged
products against the Legal Metrology (Packaged Commodities) Rules,
2011 by extracting label declarations (MRP, net quantity,
manufacturer, dates, etc.) and evaluating them against a deterministic
rule engine, producing a clear **No Issue Detected / Review Required /
Potential Non-Compliance** result with a downloadable PDF report.

**Read [docs/ROADMAP.md](docs/ROADMAP.md) before relying on this for a
demo or a decision.** It lists exactly what's real, what's optional
(falls back to a lighter local mode if unset), and what's still a
known, documented gap — updated after every phase, not written once
and left stale.

## Project Structure

```
Legal-Metrology-AI-Compliance-System/
├── backend/                 FastAPI application
│   └── app/
│       ├── core/              config, JWT auth, RBAC
│       ├── database/          SQLAlchemy base + session
│       ├── models/            one file per domain entity
│       ├── schemas/           one file per domain entity (Pydantic)
│       ├── api/                one router per resource
│       ├── services/          rule engine, OCR/CV, RAG, reports, storage, audit
│       └── workers/           Celery app + tasks
│   └── alembic/                DB migrations
├── frontend/                 Vanilla JS SPA (Bootstrap 5)
├── rules/legal_rules/      SIH_Legal_Compliance_Master.csv (rule engine's source of truth)
├── storage/                    Local-disk fallback for images/reports (see Object Storage below)
├── docs/                        Tech stack, PRD, architecture diagrams, roadmap
├── tests/backend/          Automated API test suite
└── docker/, docker-compose.yml   Full-stack container setup
```

## Running the Full Stack (recommended default)

```bash
cp backend/.env.example backend/.env   # fill in JWT_SECRET_KEY at minimum
docker compose up --build
```

This brings up FastAPI + a Celery worker + PostgreSQL + Redis + MinIO,
matching the target architecture in `docs/MetraAI_Final_Tech_Stack.pdf`.
First time only, create the MinIO bucket and apply migrations:

```bash
docker compose exec backend python -c "from app.services.storage import storage; storage.client.create_bucket(Bucket='legallens')"
docker compose exec backend alembic upgrade head
```

Then open **http://127.0.0.1:8000**.

## Running Locally Without Docker (lightweight fallback)

Every piece of infrastructure above is optional and env-gated — leave
`DATABASE_URL`/`REDIS_URL`/`S3_BUCKET` unset and the app runs against
SQLite, processes tasks inline, and stores files on local disk. Useful
for quick local development or if you don't have Docker:

```bash
pip install -r backend/requirements.txt
python run_server.py
```

Then open **http://127.0.0.1:8000**.

Demo credentials (seeded automatically on first run, either mode):
- **Citizen:** `user@legallens.demo` / `user123`
- **Officer/Admin:** `admin@legallens.demo` / `admin123`

## Running the Test Suite

```bash
python -m unittest tests.backend.test_api -v
```

Runs entirely against the lightweight fallback mode (SQLite, inline
tasks, local disk) — no Docker or external services required.

## Why the SPA has no separate HTML pages per route

The frontend is a single-page app (`frontend/index.html` +
`frontend/js/app.js`) that renders login, dashboard, inspection,
products, cases, rules, and audit views client-side, rather than as
separate static HTML files. This was a deliberate choice to keep
state (auth session, in-progress inspections) consistent across views
without full page reloads — not an oversight. If the project later
needs server-rendered routes (e.g. for SEO or multi-page deep
linking), that's a real, scoped rewrite rather than something to fake
with empty placeholder pages.

## Tech Stack

See [docs/MetraAI_Final_Tech_Stack.pdf](docs/MetraAI_Final_Tech_Stack.pdf)
for the original target architecture, and
[docs/PRODUCTION_READINESS_PRD.md](docs/PRODUCTION_READINESS_PRD.md)
for the phased plan that closed the gap between that target and this
codebase. Implemented: HTML5/CSS3/JS + Bootstrap 5, FastAPI +
Pydantic + SQLAlchemy + JWT/RBAC, PostgreSQL + Alembic (SQLite
fallback), Celery + Redis (inline fallback), OpenCV + Tesseract OCR,
ReportLab, S3/MinIO object storage (local-disk fallback), TF-IDF Legal
RAG with optional LLM-grounded answers. See
[docs/ROADMAP.md](docs/ROADMAP.md) for the honest, current-as-of-last-phase
state of every one of these, including exactly which parts of the
original tech-stack doc (PaddleOCR, YOLO, NLP/transformers) are or
aren't in yet.

## License

MIT — see [LICENSE](LICENSE).

