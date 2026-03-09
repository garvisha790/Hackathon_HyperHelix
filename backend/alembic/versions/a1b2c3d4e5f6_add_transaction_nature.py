"""add_transaction_nature_to_canonical_invoices

Revision ID: a1b2c3d4e5f6
Revises: 6d59cfd1d696
Create Date: 2026-03-09 14:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '6d59cfd1d696'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('canonical_invoices', sa.Column('transaction_nature', sa.String(length=30), nullable=True, comment='purchase | sale | bill_of_supply'))


def downgrade() -> None:
    op.drop_column('canonical_invoices', 'transaction_nature')
