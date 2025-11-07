# Chat Session Migration Instructions

## Overview
This migration adds ChatGPT-style session management to all existing company databases.

## What This Migration Does
- Adds `chat_sessions` table to all company databases
- Adds `session_id` column to existing `chat_history` table
- Preserves all existing chat history

## Prerequisites
- Python 3.8+
- Access to production environment variables
- Database credentials in `.env` file

## Running the Migration

### Option 1: On Production Server (Render.com)

```bash
# SSH or use Render shell to run:
cd backend
python migrate_chat_sessions.py
```

### Option 2: Locally (with production DB access)

```bash
# 1. Ensure .env file has correct DATABASE_URL
cd backend

# 2. Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Run migration
python migrate_chat_sessions.py
```

## Expected Output

```
============================================================
Starting Chat Session Migration
============================================================

Found 5 companies to migrate
Migrating company comp_abc123...
  📝 Creating chat_sessions table for company comp_abc123...
  ✅ Created chat_sessions table
  📝 Adding session_id column to chat_history...
  ✅ Added session_id column to chat_history
  ✅ Company comp_abc123 migration complete

Migrating company comp_def456...
  ✅ Company comp_def456 already has chat_sessions table
  ✅ chat_history already has session_id column
  ✅ Company comp_def456 migration complete

============================================================
Migration Summary
============================================================
✅ Successfully migrated: 5 companies
❌ Failed to migrate: 0 companies

✅ Migration complete!
```

## Safety Features

1. **Idempotent**: Can be run multiple times safely
2. **checkfirst=True**: Only creates tables if they don't exist
3. **Non-destructive**: Doesn't delete or modify existing data
4. **Logging**: Detailed logs of all operations

## After Migration

Once migration is complete:

1. **Restart the application** to load new models
2. **Test chat functionality**:
   - Create new chat session
   - Send messages
   - Switch between sessions
   - Verify sessions persist after refresh

## Rollback (if needed)

If you need to rollback:

```sql
-- For each company database:
ALTER TABLE chat_history DROP COLUMN session_id;
DROP TABLE chat_sessions;
```

## Troubleshooting

### Error: "relation chat_history does not exist"
- This company database hasn't been fully initialized
- Run the company initialization script first

### Error: "column session_id already exists"
- Migration has already been run for this company
- This is safe to ignore

### Error: "permission denied"
- Ensure database user has CREATE TABLE privileges
- Check connection string in .env file

## Support

If migration fails, check:
1. Database connectivity
2. User permissions
3. Error logs from migration output
4. Company database URLs in management database

For help, contact the development team with:
- Migration output logs
- Error messages
- Company IDs that failed
