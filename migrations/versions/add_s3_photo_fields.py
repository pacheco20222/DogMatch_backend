"""Add S3 photo fields to User, Event, and Photo models

Revision ID: add_s3_photo_fields
Revises: 7a6218d21406
Create Date: 2025-10-08 02:00:00.000000

S3 Bucket: dogmatch-bucket
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_s3_photo_fields'
down_revision = '7a6218d21406'
branch_labels = None
depends_on = None


def upgrade():
    # Add profile photo fields to users table
    op.add_column('users', sa.Column('profile_photo_url', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('profile_photo_filename', sa.String(length=255), nullable=True))
    
    # Add S3 fields to photos table
    op.add_column('photos', sa.Column('s3_key', sa.String(length=500), nullable=True))
    op.add_column('photos', sa.Column('content_type', sa.String(length=100), nullable=True))


def downgrade():
    # Remove S3 fields from photos table
    op.drop_column('photos', 'content_type')
    op.drop_column('photos', 's3_key')
    
    # Remove profile photo fields from users table
    op.drop_column('users', 'profile_photo_filename')
    op.drop_column('users', 'profile_photo_url')
