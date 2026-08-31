# backend/alembic/ — Not yet implemented

The current prototype creates tables directly via
`Base.metadata.create_all()` in `backend/app/main.py` on every
startup, which is fine for a demo but does not support real schema
migrations. This directory is reserved for Alembic migration scripts
once the schema needs to evolve without dropping data. See
docs/ROADMAP.md.
