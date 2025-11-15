"""convert_profile_photo_urls_to_s3_keys

Revision ID: a1b2c3d4e5f6
Revises: 954b4da10127
Create Date: 2025-11-15 00:00:00.000000

Purpose:
    Convert profile_photo_url column from storing full S3 URLs to storing S3 keys.
    This allows generating fresh signed URLs on-demand rather than storing expired URLs.
    
    Before: https://dogmatch-bucker-dev.s3.us-east-2.amazonaws.com/user-photos/7/profile_abc123.jpg
    After:  user-photos/7/profile_abc123.jpg

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '954b4da10127'
branch_labels = None
depends_on = None


def upgrade():
    """
    Convert existing full S3 URLs to S3 keys.
    
    This migration:
    1. Extracts S3 keys from any existing full URLs
    2. Updates the profile_photo_url column to store keys instead of URLs
    3. Signed URLs will be generated on-demand by the application
    """
    
    # Get database connection
    connection = op.get_bind()
    
    # Convert existing full URLs to S3 keys
    # Pattern: https://dogmatch-bucker-dev.s3.us-east-2.amazonaws.com/user-photos/7/profile_xxx.jpg
    # Extract: user-photos/7/profile_xxx.jpg
    
    # Use SUBSTRING_INDEX to extract everything after .amazonaws.com/
    # This works for both with and without query parameters (?t=timestamp)
    update_sql = """
        UPDATE users 
        SET profile_photo_url = CASE
            -- If it's a full S3 URL, extract just the key
            WHEN profile_photo_url LIKE '%amazonaws.com/%' THEN
                -- Remove query parameters first (anything after ?)
                SUBSTRING_INDEX(
                    -- Then extract everything after amazonaws.com/
                    SUBSTRING_INDEX(profile_photo_url, 'amazonaws.com/', -1),
                    '?',
                    1
                )
            -- If it's already a key or NULL, leave it as is
            ELSE profile_photo_url
        END
        WHERE profile_photo_url IS NOT NULL
    """
    
    connection.execute(text(update_sql))
    
    print("✅ Converted profile photo URLs to S3 keys")
    print("   Full URLs → S3 keys (e.g., user-photos/7/profile_xxx.jpg)")
    print("   Application will generate fresh signed URLs on retrieval")


def downgrade():
    """
    Cannot reliably reverse this migration as we'd need to reconstruct full URLs.
    The S3 bucket name and region would need to be hardcoded, which is not ideal.
    
    If you need to downgrade, manually update the URLs in the database.
    """
    
    print("⚠️  Cannot automatically downgrade - S3 keys cannot be converted back to full URLs")
    print("   If needed, manually update profile_photo_url values in the database")
    pass
