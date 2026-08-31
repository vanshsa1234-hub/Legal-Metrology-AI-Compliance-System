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

**Before you rely on this for a demo or a decision: read [docs/ROADMAP.md](docs/ROADMAP.md).**
It lists exactly what's real and what's still simulated — most
importantly, the OCR/label extraction layer is currently a demo
catalog, not live computer vision, and authentication is not yet
production-grade.

## Project Structure

```
Legal-Metrology-AI-Compliance-System/
├── backend/                 FastAPI application
│   └── app/
│       ├── core/              config, security
│       ├── database/          SQLAlchemy base + session
│       ├── models/            one file per domain entity
│       ├── schemas/           one file per domain entity (Pydantic)
│       ├── api/                one router per resource
│       ├── services/          rule engine, OCR, reports, audit, seeding
│       └── workers/           reserved for Celery (not yet implemented)
├── frontend/                 Vanilla JS SPA (Bootstrap 5)
├── rules/legal_rules/      SIH_Legal_Compliance_Master.csv (rule engine's source of truth)
├── storage/                    Runtime-generated images, evidence, reports
├── docs/                        Tech stack, PRD, architecture diagrams, roadmap
├── tests/backend/          Automated API test suite
└── docker/                    Container build
```

## Running Locally

```bash
# from the project root
pip install -r backend/requirements.txt
python run_server.py
```

Then open **http://127.0.0.1:8000**.

Demo credentials (seeded automatically on first run):
- **Citizen:** `user@legallens.demo` / `user123`
- **Officer/Admin:** `admin@legallens.demo` / `admin123`

## Running with Docker

```bash
docker compose up --build
```

## Running the Test Suite

```bash
python tests/backend/test_api.py
```

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
for the full intended architecture. Currently implemented: HTML5/CSS3/JS
+ Bootstrap 5, FastAPI + Pydantic + SQLAlchemy, SQLite, ReportLab. See
[docs/ROADMAP.md](docs/ROADMAP.md) for what's planned but not yet built
(PostgreSQL, Celery/Redis, real OCR/CV, JWT auth, object storage).

## License

MIT — see [LICENSE](LICENSE).
