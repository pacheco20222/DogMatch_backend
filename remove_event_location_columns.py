"""
Migration Script: Remove latitude, longitude, and state columns from events table
Created: October 23, 2025
Purpose: Simplify location data to only use city and country
"""

import os
import sys
from dotenv import load_dotenv
import pymysql

# Load environment variables
load_dotenv()

def get_db_connection():
    """Create database connection"""
    try:
        connection = pymysql.connect(
            host=os.environ.get('DB_HOST'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            database=os.environ.get('DB_NAME'),
            port=int(os.environ.get('DB_PORT', 3306)),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ Successfully connected to database")
        return connection
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        sys.exit(1)

def check_columns_exist(cursor):
    """Check if columns exist before attempting to drop them"""
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = 'events'
        AND COLUMN_NAME IN ('latitude', 'longitude', 'state')
    """, (os.environ.get('DB_NAME'),))
    
    existing_columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
    return existing_columns

def backup_data(cursor):
    """Backup existing location data"""
    print("\n📊 Backing up existing location data...")
    
    cursor.execute("""
        SELECT id, title, city, state, country, latitude, longitude
        FROM events
        WHERE latitude IS NOT NULL OR longitude IS NOT NULL OR state IS NOT NULL
    """)
    
    records = cursor.fetchall()
    
    if records:
        print(f"   Found {len(records)} events with location data:")
        for record in records:
            print(f"   - Event ID {record['id']}: {record['title']}")
            if record['state']:
                print(f"     State: {record['state']}")
            if record['latitude'] and record['longitude']:
                print(f"     Coordinates: ({record['latitude']}, {record['longitude']})")
    else:
        print("   No events with latitude/longitude/state data found")
    
    return records

def remove_columns(cursor, columns_to_remove):
    """Remove the specified columns from events table"""
    print("\n🔨 Removing columns from events table...")
    
    for column in columns_to_remove:
        try:
            print(f"   Dropping column: {column}")
            cursor.execute(f"ALTER TABLE events DROP COLUMN {column}")
            print(f"   ✅ Successfully dropped column: {column}")
        except Exception as e:
            print(f"   ⚠️  Error dropping column {column}: {e}")
            raise

def verify_schema(cursor):
    """Verify the final schema"""
    print("\n🔍 Verifying final schema...")
    
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = 'events'
        AND COLUMN_NAME IN ('city', 'country', 'venue_details', 'location')
        ORDER BY ORDINAL_POSITION
    """, (os.environ.get('DB_NAME'),))
    
    remaining_columns = cursor.fetchall()
    
    print("   Current location-related columns:")
    for col in remaining_columns:
        nullable = "NULL" if col['IS_NULLABLE'] == 'YES' else "NOT NULL"
        default = f" DEFAULT {col['COLUMN_DEFAULT']}" if col['COLUMN_DEFAULT'] else ""
        print(f"   - {col['COLUMN_NAME']}: {col['DATA_TYPE']} {nullable}{default}")

def main():
    """Main migration function"""
    print("=" * 70)
    print("EVENT LOCATION COLUMNS REMOVAL MIGRATION")
    print("=" * 70)
    print("\nThis script will:")
    print("  1. Backup existing location data")
    print("  2. Remove 'latitude', 'longitude', and 'state' columns")
    print("  3. Keep 'city', 'country', 'location', and 'venue_details' columns")
    print("\n" + "=" * 70)
    
    # Confirm execution
    response = input("\n⚠️  Do you want to proceed? (yes/no): ").strip().lower()
    if response != 'yes':
        print("❌ Migration cancelled by user")
        sys.exit(0)
    
    connection = get_db_connection()
    
    try:
        with connection.cursor() as cursor:
            # Check which columns exist
            existing_columns = check_columns_exist(cursor)
            
            if not existing_columns:
                print("\n✅ Columns have already been removed. Nothing to do.")
                return
            
            print(f"\n📋 Found columns to remove: {', '.join(existing_columns)}")
            
            # Backup data
            backup_records = backup_data(cursor)
            
            # Remove columns
            remove_columns(cursor, existing_columns)
            
            # Commit changes
            connection.commit()
            print("\n✅ Database changes committed successfully")
            
            # Verify final schema
            verify_schema(cursor)
            
            print("\n" + "=" * 70)
            print("✅ MIGRATION COMPLETED SUCCESSFULLY")
            print("=" * 70)
            print("\n📝 Summary:")
            print(f"   - Removed {len(existing_columns)} columns: {', '.join(existing_columns)}")
            print(f"   - Events with location data: {len(backup_records)}")
            print("   - Remaining location columns: city, country, location, venue_details")
            print("\n⚠️  Note: Location data has been simplified.")
            print("   Events now use only city and country for filtering.")
            
    except Exception as e:
        connection.rollback()
        print(f"\n❌ Error during migration: {e}")
        print("   Database changes have been rolled back")
        sys.exit(1)
    
    finally:
        connection.close()
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    main()
