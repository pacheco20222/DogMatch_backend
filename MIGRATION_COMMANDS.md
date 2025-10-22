# Flask-Migrate Quick Reference Guide

## Common Migration Commands

### Initial Setup (Already Done ✅)
```bash
# Initialize migrations (creates migrations/ directory)
flask db init

# Create initial migration
flask db migrate -m "Initial migration with all tables"

# Apply migration to database
flask db upgrade
```

---

## Daily Development Workflow

### 1. After Modifying Models
When you make changes to any model in `app/models/`:

```bash
# Generate a new migration
flask db migrate -m "Description of changes"

# Review the generated migration file in migrations/versions/
# Make sure it looks correct!

# Apply the migration
flask db upgrade
```

### 2. Rollback Changes
If you need to undo a migration:

```bash
# Rollback one migration
flask db downgrade

# Rollback to a specific version
flask db downgrade <revision_id>

# Rollback all migrations
flask db downgrade base
```

### 3. Check Current Status
```bash
# Show current migration version
flask db current

# Show migration history
flask db history

# Show pending migrations
flask db heads
```

---

## Common Scenarios

### Scenario 1: Adding a New Column
1. Edit your model file (e.g., `app/models/user.py`)
2. Add the new column:
   ```python
   bio = db.Column(db.Text, nullable=True)
   ```
3. Generate migration:
   ```bash
   flask db migrate -m "Add bio column to users table"
   ```
4. Review the migration file
5. Apply migration:
   ```bash
   flask db upgrade
   ```

### Scenario 2: Adding a New Table
1. Create new model file (e.g., `app/models/notification.py`)
2. Import in `app/models/__init__.py`
3. Generate migration:
   ```bash
   flask db migrate -m "Add notifications table"
   ```
4. Apply migration:
   ```bash
   flask db upgrade
   ```

### Scenario 3: Modifying Column Type
1. Edit model to change column type
2. Generate migration:
   ```bash
   flask db migrate -m "Change user phone to VARCHAR(30)"
   ```
3. **IMPORTANT**: Review migration carefully - data type changes can lose data!
4. Apply migration:
   ```bash
   flask db upgrade
   ```

### Scenario 4: Adding Foreign Key Relationship
1. Add relationship in model:
   ```python
   category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
   ```
2. Generate migration:
   ```bash
   flask db migrate -m "Add category relationship to dogs"
   ```
3. Apply migration:
   ```bash
   flask db upgrade
   ```

---

## Production Deployment

### On Render or Similar Platforms

1. **Automatic migrations** (recommended):
   Add to your build command:
   ```bash
   pip install -r requirements.txt && flask db upgrade
   ```

2. **Manual migrations**:
   ```bash
   # SSH into your server or use platform CLI
   flask db upgrade
   ```

### Important Production Notes
- Always test migrations locally first
- Backup database before running migrations in production
- Consider downtime for large migrations
- Use `flask db upgrade --sql` to preview SQL without executing

---

## Troubleshooting

### Problem: "Target database is not up to date"
```bash
# Check current version
flask db current

# Upgrade to latest
flask db upgrade
```

### Problem: "Can't locate revision identified by 'xxxxx'"
```bash
# Stamp database with current version
flask db stamp head
```

### Problem: Migration generates empty file
- Make sure you saved your model changes
- Verify models are imported in `app/models/__init__.py`
- Check that Flask app is properly configured

### Problem: Migration fails to apply
1. Check error message carefully
2. Review the migration file
3. Check for conflicting constraints or data
4. Consider manual SQL fixes if needed
5. Use `flask db downgrade` to rollback

---

## Best Practices

### ✅ DO
- Always review generated migrations before applying
- Write descriptive migration messages
- Test migrations locally before production
- Keep migrations in version control
- Backup database before major migrations
- Use `nullable=True` for new columns on existing tables

### ❌ DON'T
- Don't edit applied migrations
- Don't delete migration files
- Don't skip migrations (apply them in order)
- Don't commit database files to git
- Don't run migrations on production without testing

---

## Advanced Commands

### Generate SQL without executing
```bash
# See what SQL will be executed
flask db upgrade --sql

# See SQL for specific migration
flask db upgrade <revision>:+1 --sql
```

### Merge migration branches
```bash
# If you have multiple heads
flask db merge <revision1> <revision2> -m "Merge branches"
```

### Mark database at specific version (without running migrations)
```bash
# Useful for syncing migration state
flask db stamp <revision>
```

---

## Your Current Setup

### Database
- **Type**: MySQL 8.0.42
- **Host**: AWS RDS (us-east-2)
- **Database**: dogmatch_db

### Current Migration
- **Revision**: 8f8b7d456872
- **Description**: Initial migration with all tables
- **Tables**: 9 (users, dogs, photos, matches, messages, events, event_registrations, blacklisted_tokens, alembic_version)

### To Check Status
```bash
source .venv/bin/activate
flask db current
```

---

## Quick Test Commands

### Test database connection
```bash
python test_db_connection.py
```

### Verify Flask app database
```bash
python verify_flask_db.py
```

### Start backend server
```bash
python run.py
# or
flask run
```

---

## Need Help?

### Flask-Migrate Documentation
https://flask-migrate.readthedocs.io/

### Alembic Documentation
https://alembic.sqlalchemy.org/

### SQLAlchemy Documentation
https://docs.sqlalchemy.org/
