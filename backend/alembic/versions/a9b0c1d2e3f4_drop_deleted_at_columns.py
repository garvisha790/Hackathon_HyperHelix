"""drop_deleted_at_columns

Remove soft delete columns and indexes from all tables.

Revision ID: a9b0c1d2e3f4
Revises: 6d59cfd1d696
Create Date: 2026-03-10 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a9b0c1d2e3f4'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    'tenants',
    'users',
    'documents',
    'canonical_invoices',
    'ledger_transactions',
    'chart_of_accounts',
]


def upgrade() -> None:
    conn = op.get_bind()
    for table in TABLES:
        # Safely drop index if it exists
        idx_name = f'ix_{table}_deleted_at'
        result = conn.execute(sa.text(
            "SELECT 1 FROM pg_indexes WHERE indexname = :name"
        ), {"name": idx_name})
        if result.fetchone():
            op.drop_index(idx_name, table_name=table)
        # Safely drop column if it exists
        result = conn.execute(sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = 'deleted_at'"
        ), {"table": table})
        if result.fetchone():
            op.drop_column(table, 'deleted_at')


def downgrade() -> None:
    for table in TABLES:
        op.add_column(table, sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
        op.create_index(op.f(f'ix_{table}_deleted_at'), table, ['deleted_at'])
