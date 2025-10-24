# Event Location Columns Migration

## Overview
This migration removes the `latitude`, `longitude`, and `state` columns from the `events` table to simplify location data management.

## Changes Made

### Database Schema Changes
**Removed Columns:**
- `latitude` (Float) - GPS latitude coordinate
- `longitude` (Float) - GPS longitude coordinate
- `state` (String) - State/province field

**Retained Columns:**
- `city` (String) - City name
- `country` (String) - Country name (default: Mexico)
- `location` (String) - Full address or venue name
- `venue_details` (Text) - Additional venue information

### Model Changes
**File:** `app/models/event.py`
- Removed `latitude`, `longitude`, and `state` fields from Event model
- Updated `get_distance_to()` method to return None (deprecated)
- Updated all Marshmallow schemas (EventCreateSchema, EventUpdateSchema, EventListSchema)
- Updated `to_dict()` method to exclude removed fields

### Route Changes
**File:** `app/routes/events.py`
- Removed latitude/longitude handling in `create_event()`
- Removed state filter in `get_events()`
- Removed geospatial filtering logic

## Running the Migration

### Prerequisites
1. Ensure you have a database backup
2. Have your `.env` file configured with database credentials
3. Install required dependencies: `pip install pymysql python-dotenv`

### Execution Steps

1. **Navigate to backend directory:**
   ```bash
   cd DogMatch_backend
   ```

2. **Run the migration script:**
   ```bash
   python remove_event_location_columns.py
   ```

3. **Follow the prompts:**
   - The script will show you what will be changed
   - Type `yes` to confirm and proceed
   - The script will backup existing data before making changes

### What the Script Does

1. **Connects to Database**
   - Uses credentials from `.env` file
   - Validates connection before proceeding

2. **Checks Existing Columns**
   - Verifies which columns exist before attempting removal
   - Safe to run multiple times (idempotent)

3. **Backs Up Data**
   - Lists all events with location data
   - Shows which events have latitude/longitude or state data

4. **Removes Columns**
   - Drops `latitude`, `longitude`, and `state` columns
   - Uses ALTER TABLE statements

5. **Verifies Schema**
   - Confirms remaining location columns
   - Shows final database structure

6. **Commits Changes**
   - All changes are committed in a single transaction
   - Automatic rollback on error

### Example Output

```
======================================================================
EVENT LOCATION COLUMNS REMOVAL MIGRATION
======================================================================

This script will:
  1. Backup existing location data
  2. Remove 'latitude', 'longitude', and 'state' columns
  3. Keep 'city', 'country', 'location', and 'venue_details' columns

======================================================================

⚠️  Do you want to proceed? (yes/no): yes

✅ Successfully connected to database

📋 Found columns to remove: latitude, longitude, state

📊 Backing up existing location data...
   Found 3 events with location data:
   - Event ID 1: Dog Training Workshop
     State: California
     Coordinates: (34.0522, -118.2437)
   - Event ID 2: Adoption Fair
     Coordinates: (40.7128, -74.0060)

🔨 Removing columns from events table...
   Dropping column: latitude
   ✅ Successfully dropped column: latitude
   Dropping column: longitude
   ✅ Successfully dropped column: longitude
   Dropping column: state
   ✅ Successfully dropped column: state

✅ Database changes committed successfully

🔍 Verifying final schema...
   Current location-related columns:
   - location: varchar(300) NOT NULL
   - city: varchar(100) NULL
   - country: varchar(100) NULL DEFAULT 'Mexico'
   - venue_details: text NULL

======================================================================
✅ MIGRATION COMPLETED SUCCESSFULLY
======================================================================

📝 Summary:
   - Removed 3 columns: latitude, longitude, state
   - Events with location data: 3
   - Remaining location columns: city, country, location, venue_details

⚠️  Note: Location data has been simplified.
   Events now use only city and country for filtering.

🔌 Database connection closed
```

## Impact on Application

### Frontend Changes Needed
The frontend should be updated to:
- Remove latitude/longitude input fields from event creation forms
- Remove state field from event creation/editing forms
- Update location filtering to use only city and country
- Remove any map-based distance filtering features

### API Changes
- Event creation/update no longer accepts `latitude`, `longitude`, or `state`
- Event listing filter no longer supports `max_distance`, `user_latitude`, `user_longitude`, or `state`
- Event responses no longer include `latitude`, `longitude`, or `state` fields

### Backward Compatibility
- ⚠️ **Breaking Change**: This is a breaking change for clients expecting location coordinates
- Existing events will retain their `city` and `country` data
- Location filtering now works by city and country text matching only

## Rollback

If you need to rollback this migration:

1. **Add columns back:**
   ```sql
   ALTER TABLE events ADD COLUMN latitude FLOAT NULL;
   ALTER TABLE events ADD COLUMN longitude FLOAT NULL;
   ALTER TABLE events ADD COLUMN state VARCHAR(100) NULL;
   ```

2. **Restore model and route changes:**
   - Revert changes in `app/models/event.py`
   - Revert changes in `app/routes/events.py`

3. **Note:** Original coordinate data cannot be recovered unless you have a backup

## Support

If you encounter any issues during migration:
1. Check database connection credentials in `.env`
2. Ensure you have proper database permissions (ALTER TABLE)
3. Review the error messages from the script
4. Contact the development team if needed

## Migration Date
**Created:** October 23, 2025
**Applied:** _[To be filled when executed]_
**Applied By:** _[To be filled when executed]_
