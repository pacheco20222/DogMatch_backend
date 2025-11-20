"""add_message_indexes

Revision ID: add_message_indexes
Revises: a1b2c3d4e5f6
Create Date: 2025-11-19 12:00:00.000000

Purpose:
    Add database indexes to optimize message queries:
    - Composite index on (match_id, sent_at) for faster message retrieval
    - Composite index on (match_id, is_deleted, sent_at) for conversations
    - Composite index on (match_id, sender_user_id, is_read, is_deleted) for unread counts
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_message_indexes'
down_revision = 'a1b2c3d4e5f6'  # This should match the latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Add composite index for message queries by match_id and sent_at
    op.create_index(
        'idx_messages_match_sent_at',
        'messages',
        ['match_id', 'sent_at'],
        unique=False
    )
    
    # Add composite index for conversations (filtering deleted messages)
    op.create_index(
        'idx_messages_match_deleted_sent',
        'messages',
        ['match_id', 'is_deleted', 'sent_at'],
        unique=False
    )
    
    # Add composite index for unread count queries
    op.create_index(
        'idx_messages_match_sender_read_deleted',
        'messages',
        ['match_id', 'sender_user_id', 'is_read', 'is_deleted'],
        unique=False
    )


def downgrade():
    op.drop_index('idx_messages_match_sender_read_deleted', table_name='messages')
    op.drop_index('idx_messages_match_deleted_sent', table_name='messages')
    op.drop_index('idx_messages_match_sent_at', table_name='messages')

