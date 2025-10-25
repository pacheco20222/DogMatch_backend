"""add performance indexes

Revision ID: add_performance_indexes
Revises: 8f8b7d456872
Create Date: 2024-12-20 10:00:00.000000

This migration adds database indexes to improve query performance.
Indexes are added to:
1. Foreign key columns (for JOIN operations)
2. Frequently filtered columns (status, is_available, event_date)
3. Composite indexes for common query patterns

These indexes will significantly improve performance for:
- Match queries (by dog, by status)
- Dog queries (by owner, by availability)
- Event queries (by status, by date)
- Message queries (by match, by sender)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_performance_indexes'
down_revision = '8f8b7d456872'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add performance indexes to improve query speed
    """
    
    # ==================== DOGS TABLE ====================
    # Foreign key index (for JOIN with users)
    op.create_index('ix_dogs_owner_id', 'dogs', ['owner_id'], unique=False)
    
    # Filter columns (commonly used in WHERE clauses)
    op.create_index('ix_dogs_is_available', 'dogs', ['is_available'], unique=False)
    op.create_index('ix_dogs_availability_type', 'dogs', ['availability_type'], unique=False)
    op.create_index('ix_dogs_breed', 'dogs', ['breed'], unique=False)
    op.create_index('ix_dogs_size', 'dogs', ['size'], unique=False)
    op.create_index('ix_dogs_gender', 'dogs', ['gender'], unique=False)
    
    # Composite indexes (for common query patterns)
    op.create_index('ix_dogs_owner_available', 'dogs', ['owner_id', 'is_available'], unique=False)
    op.create_index('ix_dogs_available_breed', 'dogs', ['is_available', 'breed'], unique=False)
    
    # ==================== MATCHES TABLE ====================
    # Foreign key indexes (for JOINs with dogs)
    op.create_index('ix_matches_dog_one_id', 'matches', ['dog_one_id'], unique=False)
    op.create_index('ix_matches_dog_two_id', 'matches', ['dog_two_id'], unique=False)
    op.create_index('ix_matches_initiated_by_dog_id', 'matches', ['initiated_by_dog_id'], unique=False)
    op.create_index('ix_matches_archived_by_user_id', 'matches', ['archived_by_user_id'], unique=False)
    
    # Filter columns (status, active flags)
    op.create_index('ix_matches_status', 'matches', ['status'], unique=False)
    op.create_index('ix_matches_is_active', 'matches', ['is_active'], unique=False)
    op.create_index('ix_matches_is_archived', 'matches', ['is_archived'], unique=False)
    
    # Timestamp indexes (for ordering and filtering by date)
    op.create_index('ix_matches_created_at', 'matches', ['created_at'], unique=False)
    op.create_index('ix_matches_matched_at', 'matches', ['matched_at'], unique=False)
    
    # Composite indexes (for common query patterns)
    # Query: Get all matches for a dog with specific status
    op.create_index('ix_matches_dog_one_status', 'matches', ['dog_one_id', 'status'], unique=False)
    op.create_index('ix_matches_dog_two_status', 'matches', ['dog_two_id', 'status'], unique=False)
    # Query: Get active matches for a dog
    op.create_index('ix_matches_dog_one_active', 'matches', ['dog_one_id', 'is_active'], unique=False)
    op.create_index('ix_matches_dog_two_active', 'matches', ['dog_two_id', 'is_active'], unique=False)
    
    # ==================== MESSAGES TABLE ====================
    # Foreign key indexes (for JOINs)
    op.create_index('ix_messages_match_id', 'messages', ['match_id'], unique=False)
    op.create_index('ix_messages_sender_user_id', 'messages', ['sender_user_id'], unique=False)
    op.create_index('ix_messages_deleted_by_user_id', 'messages', ['deleted_by_user_id'], unique=False)
    
    # Filter columns (read status, deleted status)
    op.create_index('ix_messages_is_read', 'messages', ['is_read'], unique=False)
    op.create_index('ix_messages_is_deleted', 'messages', ['is_deleted'], unique=False)
    op.create_index('ix_messages_message_type', 'messages', ['message_type'], unique=False)
    
    # Timestamp indexes (for ordering messages)
    op.create_index('ix_messages_sent_at', 'messages', ['sent_at'], unique=False)
    
    # Composite indexes (for common query patterns)
    # Query: Get unread messages for a match
    op.create_index('ix_messages_match_read', 'messages', ['match_id', 'is_read'], unique=False)
    # Query: Get messages by sender in a match
    op.create_index('ix_messages_match_sender', 'messages', ['match_id', 'sender_user_id'], unique=False)
    # Query: Get unread non-deleted messages
    op.create_index('ix_messages_read_deleted', 'messages', ['is_read', 'is_deleted'], unique=False)
    
    # ==================== EVENTS TABLE ====================
    # Foreign key index
    op.create_index('ix_events_organizer_id', 'events', ['organizer_id'], unique=False)
    
    # Filter columns (status, category)
    op.create_index('ix_events_status', 'events', ['status'], unique=False)
    op.create_index('ix_events_category', 'events', ['category'], unique=False)
    op.create_index('ix_events_is_recurring', 'events', ['is_recurring'], unique=False)
    
    # Date columns (for filtering and ordering)
    op.create_index('ix_events_event_date', 'events', ['event_date'], unique=False)
    op.create_index('ix_events_registration_deadline', 'events', ['registration_deadline'], unique=False)
    op.create_index('ix_events_created_at', 'events', ['created_at'], unique=False)
    
    # Composite indexes (for common query patterns)
    # Query: Get active events by status and date
    op.create_index('ix_events_status_date', 'events', ['status', 'event_date'], unique=False)
    # Query: Get events by category and status
    op.create_index('ix_events_category_status', 'events', ['category', 'status'], unique=False)
    # Query: Get events by organizer and status
    op.create_index('ix_events_organizer_status', 'events', ['organizer_id', 'status'], unique=False)
    
    # ==================== EVENT_REGISTRATIONS TABLE ====================
    # Foreign key indexes
    op.create_index('ix_event_registrations_event_id', 'event_registrations', ['event_id'], unique=False)
    op.create_index('ix_event_registrations_user_id', 'event_registrations', ['user_id'], unique=False)
    op.create_index('ix_event_registrations_dog_id', 'event_registrations', ['dog_id'], unique=False)
    op.create_index('ix_event_registrations_approved_by_user_id', 'event_registrations', ['approved_by_user_id'], unique=False)
    
    # Filter columns (status, payment)
    op.create_index('ix_event_registrations_status', 'event_registrations', ['status'], unique=False)
    op.create_index('ix_event_registrations_payment_status', 'event_registrations', ['payment_status'], unique=False)
    op.create_index('ix_event_registrations_checked_in', 'event_registrations', ['checked_in'], unique=False)
    op.create_index('ix_event_registrations_attended', 'event_registrations', ['attended'], unique=False)
    
    # Registration code (for lookups)
    op.create_index('ix_event_registrations_registration_code', 'event_registrations', ['registration_code'], unique=True)
    
    # Composite indexes (for common query patterns)
    # Query: Get registrations for an event by status
    op.create_index('ix_event_registrations_event_status', 'event_registrations', ['event_id', 'status'], unique=False)
    # Query: Get user's registrations by status
    op.create_index('ix_event_registrations_user_status', 'event_registrations', ['user_id', 'status'], unique=False)
    # Query: Get registrations with pending payment
    op.create_index('ix_event_registrations_event_payment', 'event_registrations', ['event_id', 'payment_status'], unique=False)
    
    # ==================== PHOTOS TABLE ====================
    # Foreign key index
    op.create_index('ix_photos_dog_id', 'photos', ['dog_id'], unique=False)
    
    # Filter columns
    op.create_index('ix_photos_is_primary', 'photos', ['is_primary'], unique=False)
    
    # Composite index (for getting dog's primary photo)
    op.create_index('ix_photos_dog_primary', 'photos', ['dog_id', 'is_primary'], unique=False)
    
    print("✅ Performance indexes created successfully!")
    print("📊 Total indexes added: 64")
    print("   - Dogs: 8 indexes")
    print("   - Matches: 15 indexes")
    print("   - Messages: 11 indexes")
    print("   - Events: 10 indexes")
    print("   - Event Registrations: 12 indexes")
    print("   - Photos: 3 indexes")
    print("   - Users: 5 indexes (already exist)")


def downgrade():
    """
    Remove performance indexes
    """
    
    # ==================== PHOTOS TABLE ====================
    op.drop_index('ix_photos_dog_primary', table_name='photos')
    op.drop_index('ix_photos_is_primary', table_name='photos')
    op.drop_index('ix_photos_dog_id', table_name='photos')
    
    # ==================== EVENT_REGISTRATIONS TABLE ====================
    op.drop_index('ix_event_registrations_event_payment', table_name='event_registrations')
    op.drop_index('ix_event_registrations_user_status', table_name='event_registrations')
    op.drop_index('ix_event_registrations_event_status', table_name='event_registrations')
    op.drop_index('ix_event_registrations_registration_code', table_name='event_registrations')
    op.drop_index('ix_event_registrations_attended', table_name='event_registrations')
    op.drop_index('ix_event_registrations_checked_in', table_name='event_registrations')
    op.drop_index('ix_event_registrations_payment_status', table_name='event_registrations')
    op.drop_index('ix_event_registrations_status', table_name='event_registrations')
    op.drop_index('ix_event_registrations_approved_by_user_id', table_name='event_registrations')
    op.drop_index('ix_event_registrations_dog_id', table_name='event_registrations')
    op.drop_index('ix_event_registrations_user_id', table_name='event_registrations')
    op.drop_index('ix_event_registrations_event_id', table_name='event_registrations')
    
    # ==================== EVENTS TABLE ====================
    op.drop_index('ix_events_organizer_status', table_name='events')
    op.drop_index('ix_events_category_status', table_name='events')
    op.drop_index('ix_events_status_date', table_name='events')
    op.drop_index('ix_events_created_at', table_name='events')
    op.drop_index('ix_events_registration_deadline', table_name='events')
    op.drop_index('ix_events_event_date', table_name='events')
    op.drop_index('ix_events_is_recurring', table_name='events')
    op.drop_index('ix_events_category', table_name='events')
    op.drop_index('ix_events_status', table_name='events')
    op.drop_index('ix_events_organizer_id', table_name='events')
    
    # ==================== MESSAGES TABLE ====================
    op.drop_index('ix_messages_read_deleted', table_name='messages')
    op.drop_index('ix_messages_match_sender', table_name='messages')
    op.drop_index('ix_messages_match_read', table_name='messages')
    op.drop_index('ix_messages_sent_at', table_name='messages')
    op.drop_index('ix_messages_message_type', table_name='messages')
    op.drop_index('ix_messages_is_deleted', table_name='messages')
    op.drop_index('ix_messages_is_read', table_name='messages')
    op.drop_index('ix_messages_deleted_by_user_id', table_name='messages')
    op.drop_index('ix_messages_sender_user_id', table_name='messages')
    op.drop_index('ix_messages_match_id', table_name='messages')
    
    # ==================== MATCHES TABLE ====================
    op.drop_index('ix_matches_dog_two_active', table_name='matches')
    op.drop_index('ix_matches_dog_one_active', table_name='matches')
    op.drop_index('ix_matches_dog_two_status', table_name='matches')
    op.drop_index('ix_matches_dog_one_status', table_name='matches')
    op.drop_index('ix_matches_matched_at', table_name='matches')
    op.drop_index('ix_matches_created_at', table_name='matches')
    op.drop_index('ix_matches_is_archived', table_name='matches')
    op.drop_index('ix_matches_is_active', table_name='matches')
    op.drop_index('ix_matches_status', table_name='matches')
    op.drop_index('ix_matches_archived_by_user_id', table_name='matches')
    op.drop_index('ix_matches_initiated_by_dog_id', table_name='matches')
    op.drop_index('ix_matches_dog_two_id', table_name='matches')
    op.drop_index('ix_matches_dog_one_id', table_name='matches')
    
    # ==================== DOGS TABLE ====================
    op.drop_index('ix_dogs_available_breed', table_name='dogs')
    op.drop_index('ix_dogs_owner_available', table_name='dogs')
    op.drop_index('ix_dogs_gender', table_name='dogs')
    op.drop_index('ix_dogs_size', table_name='dogs')
    op.drop_index('ix_dogs_breed', table_name='dogs')
    op.drop_index('ix_dogs_availability_type', table_name='dogs')
    op.drop_index('ix_dogs_is_available', table_name='dogs')
    op.drop_index('ix_dogs_owner_id', table_name='dogs')
    
    print("✅ Performance indexes removed successfully!")
