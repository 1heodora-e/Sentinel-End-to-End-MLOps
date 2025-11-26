# SQLite Database Setup Guide

## Overview

Sentinel uses SQLite to store training data uploads and retraining session history. This satisfies the rubric requirement for "Data file Uploading + Saving to Database".

**Why SQLite?**
- ✅ Built into Python - no installation needed!
- ✅ No server required - it's just a file
- ✅ Perfect for development and small projects
- ✅ Easy to backup (just copy the file)
- ✅ Works immediately with zero configuration

## Database Schema

### Tables

1. **training_data_uploads**
   - Stores metadata about uploaded training data zip files
   - Tracks file information, upload timestamps, and processing status
   - Records file counts (safe, danger, total)

2. **retraining_sessions**
   - Stores retraining session history
   - Tracks training metrics (accuracy, loss, epochs)
   - Links to training data uploads

## Setup Instructions

### Step 1: Initialize Database (One-Time)

```bash
cd backend
python init_database.py
```

That's it! This creates `backend/sentinel.db` automatically.

**What happens:**
- Creates the database file (`sentinel.db`)
- Creates all necessary tables
- Ready to use immediately!

### Step 2: Verify It Works

The database file will be created at: `backend/sentinel.db`

You can verify it exists:
```bash
ls -lh backend/sentinel.db
```

## Viewing Your Database

### Option 1: SQLite Browser (Recommended - GUI)

1. **Download SQLite Browser:**
   - Windows/Mac/Linux: https://sqlitebrowser.org/
   - Or search "DB Browser for SQLite" in your app store

2. **Open the database:**
   - Open SQLite Browser
   - Click "Open Database"
   - Navigate to `backend/sentinel.db`
   - Browse tables and data visually!

### Option 2: Command Line

```bash
# Navigate to backend directory
cd backend

# Open SQLite database
sqlite3 sentinel.db

# View all tables
.tables

# View all uploads
SELECT * FROM training_data_uploads;

# View retraining sessions with details
SELECT 
    id,
    upload_id,
    start_time,
    status,
    final_val_accuracy,
    total_samples
FROM retraining_sessions
ORDER BY start_time DESC;

# Count successful retraining sessions
SELECT COUNT(*) FROM retraining_sessions WHERE status = 'completed';

# Exit SQLite
.quit
```

### Option 3: Python Script

```python
from database import SessionLocal, TrainingDataUpload, RetrainingSession

db = SessionLocal()

# Get all uploads
uploads = db.query(TrainingDataUpload).all()
for upload in uploads:
    print(f"Upload {upload.id}: {upload.filename} - Status: {upload.status}")

# Get all retraining sessions
sessions = db.query(RetrainingSession).all()
for session in sessions:
    print(f"Session {session.id}: Accuracy = {session.final_val_accuracy}")

db.close()
```

## Database Location

The database file is stored at:
```
backend/sentinel.db
```

You can:
- **Backup:** Just copy `sentinel.db` to another location
- **Reset:** Delete `sentinel.db` and run `init_database.py` again
- **Move:** Change the `DB_PATH` in `database.py` if needed

## Example Queries

### View Recent Uploads
```sql
SELECT 
    id,
    filename,
    upload_timestamp,
    status,
    total_files_count,
    safe_files_count,
    danger_files_count
FROM training_data_uploads
ORDER BY upload_timestamp DESC
LIMIT 10;
```

### View Retraining History
```sql
SELECT 
    rs.id,
    rs.start_time,
    rs.end_time,
    rs.status,
    rs.final_val_accuracy,
    rs.total_samples,
    tdu.filename
FROM retraining_sessions rs
JOIN training_data_uploads tdu ON rs.upload_id = tdu.id
ORDER BY rs.start_time DESC;
```

### Get Statistics
```sql
-- Total uploads
SELECT COUNT(*) as total_uploads FROM training_data_uploads;

-- Successful retraining sessions
SELECT COUNT(*) as successful_sessions 
FROM retraining_sessions 
WHERE status = 'completed';

-- Average accuracy
SELECT AVG(final_val_accuracy) as avg_accuracy
FROM retraining_sessions
WHERE status = 'completed';
```

## Troubleshooting

### Database File Not Created

**Problem:** `sentinel.db` doesn't exist after running `init_database.py`

**Solution:**
- Check file permissions in `backend/` directory
- Make sure you have write access
- Run `init_database.py` from the `backend/` directory

### "Database is locked" Error

**Problem:** SQLite shows "database is locked" error

**Solution:**
- This usually means another process is using the database
- Close any SQLite browsers or other connections
- Restart the FastAPI server

### Reset Database

To start fresh:
```bash
# Delete the database file
rm backend/sentinel.db

# Recreate it
python backend/init_database.py
```

## Advantages of SQLite

1. **Zero Configuration** - Works immediately
2. **No Server** - Just a file on disk
3. **Portable** - Easy to backup and move
4. **Fast** - Perfect for single-user applications
5. **Built-in** - No additional packages needed

## When to Use PostgreSQL Instead

Consider PostgreSQL if you need:
- Multiple users accessing the database simultaneously
- Very high write concurrency
- Advanced features (full-text search, complex queries)
- Production deployment with high traffic

For this project, SQLite is perfect! 🎉
