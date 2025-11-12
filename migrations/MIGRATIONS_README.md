# Database Migrations Guide

## Overview
This project uses Flask-Migrate (Alembic) to manage database schema changes. All migrations are version-controlled to ensure consistent database schemas across environments.

## Migration Files

### Initial Migration
- **File**: `8f8b7d456872_initial_migration_with_all_tables.py`
- **Purpose**: Creates all tables with the correct schema from scratch
- **Key Schema**:
  - `dogs.age_years` (INTEGER) - not `age` or `age_months`
  - `dogs.good_with_*` fields are ENUM('yes', 'no', 'not_sure') - not BOOLEAN

### Performance Indexes
- **File**: `add_performance_indexes.py`
- **Purpose**: Adds database indexes for common queries

### Schema Sync Migration
- **File**: `add_age_years_column.py`
- **Purpose**: Migrates existing databases from old schema to new schema
- **Features**:
  - Idempotent (safe to run multiple times)
  - Checks if columns exist before adding
  - Migrates data from old `age` column to `age_years`
  - Converts boolean compatibility fields to ENUM

## Running Migrations

### Fresh Database (New Deployment)
```bash
# From DogMatch_backend directory
docker compose exec backend flask db upgrade
```

This will:
1. Run the initial migration (creates all tables with correct schema)
2. Run performance indexes migration
3. Run schema sync migration (will skip already-applied changes)

### Existing Database (Update)
Same command as above - the schema sync migration is idempotent and will only apply needed changes.

### Create New Migration
```bash
# After changing models in app/models/
docker compose exec backend flask db migrate -m "description_of_changes"

# Review the generated migration file in migrations/versions/
# Edit if needed to handle data migration or special cases

# Apply the migration
docker compose exec backend flask db upgrade
```

### Rollback Migration
```bash
# Rollback one migration
docker compose exec backend flask db downgrade -1

# Rollback to specific revision
docker compose exec backend flask db downgrade <revision_id>
```

## Best Practices

1. **Always review generated migrations** - Alembic may not detect all changes correctly
2. **Test migrations on a copy of production data** before deploying
3. **Make migrations idempotent** when possible (check if changes already exist)
4. **Handle data migration** - If changing column types, migrate data first
5. **Don't modify old migrations** - Create new ones instead (except for fixes before deployment)

## Troubleshooting

### "Duplicate column name" error
The column was already added in a previous migration attempt. The schema sync migration handles this.

### "Cannot drop index needed in a foreign key" error
Don't drop indexes used by foreign keys. The schema sync migration avoids this.

### Database out of sync
```bash
# Check current database version
docker compose exec backend flask db current

# Check pending migrations
docker compose exec backend flask db heads

# Force stamp to specific version (USE WITH CAUTION)
docker compose exec backend flask db stamp <revision_id>
```

## Migration Order
1. `8f8b7d456872_initial_migration_with_all_tables.py` (base schema)
2. `add_performance_indexes.py` (performance)
3. `add_age_years_column.py` (schema sync for existing DBs)
