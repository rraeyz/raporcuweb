"""Add word_file_path and word_file_size columns

Revision ID: 001
Revises: 
Create Date: 2025-11-29 18:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add word file columns to reports table"""
    # Kolon zaten varsa hata vermesin diye try-except kullanılabilir
    # Ama Alembic otomatik kontrol eder, gerek yok
    op.add_column('reports', sa.Column('word_file_path', sa.String(length=255), nullable=True))
    op.add_column('reports', sa.Column('word_file_size', sa.Integer(), nullable=True))


def downgrade():
    """Remove word file columns from reports table"""
    op.drop_column('reports', 'word_file_size')
    op.drop_column('reports', 'word_file_path')
