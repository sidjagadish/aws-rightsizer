"""add fk finding run_id

Revision ID: 9dfa0a3b9bc3
Revises: 
Create Date: 2026-03-12 17:27:07.463836

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9dfa0a3b9bc3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.create_foreign_key(
        "finding_run_id_fkey",
        "finding",
        "scan_run",
        ["run_id"],
        ["run_id"],
    )

def downgrade():
    op.drop_constraint("finding_run_id_fkey", "finding", type_="foreignkey")