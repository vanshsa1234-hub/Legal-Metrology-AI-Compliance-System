"""
Legal Lens - Celery App (Phase 4: docs/PRODUCTION_READINESS_PRD.md)

REDIS_URL unset (local/dev/tests, matching docker-compose.yml's current
single-service setup): tasks run eagerly, inline, in the caller's
process - no Redis required, no behavior change from before Phase 4.

REDIS_URL set (docker-compose with a redis + worker service): tasks are
queued and run by a separate worker process, as intended in production.
"""
import os
from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL")

celery_app = Celery("legallens", broker=REDIS_URL or "memory://", backend=REDIS_URL)
celery_app.conf.task_always_eager = REDIS_URL is None
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
