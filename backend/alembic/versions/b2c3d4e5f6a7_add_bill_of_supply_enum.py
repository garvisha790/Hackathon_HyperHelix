"""add bill_of_supply to invoice_doc_type_enum

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-09 13:00:00.000000
"""
from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE invoice_doc_type_enum ADD VALUE IF NOT EXISTS 'bill_of_supply'")


def downgrade() -> None:
    pass  # Cannot remove enum values in PostgreSQL
