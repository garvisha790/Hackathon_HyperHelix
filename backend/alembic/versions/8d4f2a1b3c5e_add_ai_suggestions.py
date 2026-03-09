"""add_ai_suggestions

Revision ID: 8d4f2a1b3c5e
Revises: 7cf9e6368b62
Create Date: 2026-03-06 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = '8d4f2a1b3c5e'
down_revision: Union[str, None] = '7cf9e6368b62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('validations', sa.Column('ai_suggestions', JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column('validations', 'ai_suggestions')
