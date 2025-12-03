"""Add force_password_change column to users table

Revision ID: 004
Revises: 003
Create Date: 2025-12-03

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade():
    # Add force_password_change column to users table
    op.execute("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS force_password_change BOOLEAN NOT NULL DEFAULT FALSE;
    """)

def downgrade():
    # Remove force_password_change column
    op.execute("""
        ALTER TABLE users 
        DROP COLUMN IF EXISTS force_password_change;
    """)
