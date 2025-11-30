"""Add Shopier API fields

Revision ID: 002
Revises: 001
Create Date: 2025-11-30

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Add Shopier API fields to settings table
    op.execute("""
        ALTER TABLE settings 
        ADD COLUMN IF NOT EXISTS shopier_api_key VARCHAR(255),
        ADD COLUMN IF NOT EXISTS shopier_api_secret VARCHAR(255);
    """)

def downgrade():
    # Remove Shopier API fields
    op.execute("""
        ALTER TABLE settings 
        DROP COLUMN IF EXISTS shopier_api_key,
        DROP COLUMN IF EXISTS shopier_api_secret;
    """)
