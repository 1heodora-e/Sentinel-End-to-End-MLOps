# backend/init_database.py
"""
Script to initialize the SQLite database.
Run this once to create the database tables.

Usage:
    python init_database.py
"""

from database import init_db, DB_PATH
import sys

if __name__ == "__main__":
    try:
        print("Initializing SQLite database...")
        init_db()
        print("✅ Database initialized successfully!")
        print(f"\nDatabase file created at: {DB_PATH}")
        print("\nTables created:")
        print("  - training_data_uploads")
        print("  - retraining_sessions")
        print("\n💡 Tip: You can view the database using:")
        print("   - SQLite Browser: https://sqlitebrowser.org/")
        print(f"   - Command line: sqlite3 {DB_PATH}")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        print("\nNote: SQLite is built into Python, so no additional setup is needed!")
        print(
            "Make sure you have installed dependencies: pip install -r requirements.txt"
        )
        sys.exit(1)
