"""enable pgvector extension

Revision ID: 97ad8052d72d
Revises: 4dd3f45e8d43
Create Date: 2026-09-02 04:58:18.151130

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97ad8052d72d'
down_revision: Union[str, Sequence[str], None] = '4dd3f45e8d43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Enable pgvector on Postgres only. SQLite (local/dev/tests) has no
    concept of extensions, so this is a genuine no-op there rather
    than an error - Phase 7 (docs/PRODUCTION_READINESS_PRD.md) doesn't
    require Postgres to run: retrieval works today via an in-Python
    TF-IDF cosine similarity over the (currently ~30-row) rules table.
    This just makes a native `vector` column + ANN index available as
    a drop-in upgrade if that corpus ever grows large enough to need one.
    """
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP EXTENSION IF EXISTS vector")
