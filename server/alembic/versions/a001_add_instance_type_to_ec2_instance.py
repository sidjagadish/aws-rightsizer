"""add instance_type to ec2_instance

Revision ID: a001
Revises: drift000
Create Date: 2026-05-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a001'
down_revision: Union[str, Sequence[str], None] = 'drift000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ec2_instance', sa.Column('instance_type', sa.String(), nullable=False))


def downgrade() -> None:
    op.drop_column('ec2_instance', 'instance_type')
