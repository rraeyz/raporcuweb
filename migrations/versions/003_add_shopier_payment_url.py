"""Add shopier_payment_url and shopier_webhook_secret

Revision ID: 003
Revises: 002
Create Date: 2025-11-30

"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    # Add shopier_payment_url and shopier_webhook_secret to settings
    op.execute("""
        ALTER TABLE settings 
        ADD COLUMN IF NOT EXISTS shopier_payment_url VARCHAR(500),
        ADD COLUMN IF NOT EXISTS shopier_webhook_secret VARCHAR(255);
    """)

def downgrade():
    op.execute("""
        ALTER TABLE settings 
        DROP COLUMN IF EXISTS shopier_payment_url,
        DROP COLUMN IF EXISTS shopier_webhook_secret;
    """)
