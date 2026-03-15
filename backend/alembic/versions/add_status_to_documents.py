"""add status to documents

Revision ID: add_status_column
Revises: 3c124bd2831e
Create Date: 2026-02-20 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_status_column'
down_revision: Union[str, Sequence[str], None] = '3c124bd2831e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add status column to documents table if it doesn't exist."""
    # Check if column exists before adding
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('documents')]
    
    if 'status' not in columns:
        op.add_column('documents', 
            sa.Column('status', sa.String(), nullable=False, server_default='queued')
        )


def downgrade() -> None:
    """Remove status column from documents table."""
    op.drop_column('documents', 'status')
