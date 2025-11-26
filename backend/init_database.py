# backend/init_database.py
"""
Script to initialize the PostgreSQL database.
Run this once to create the database tables.

Usage:
    python init_database.py

Prerequisites:
    1. PostgreSQL must be installed and running
    2. Create a database (e.g., 'sentinel_db')
    3. Set DATABASE_URL environment variable or update the default in database.py
"""

from database import init_db, DATABASE_URL
import sys

if __name__ == "__main__":
    try:
        print("Initializing PostgreSQL database...")
        print(f"Connecting to: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
        init_db()
        print("✅ Database initialized successfully!")
        print("\nTables created:")
        print("  - training_data_uploads")
        print("  - retraining_sessions")
        print("\n💡 You can view the database using:")
        print("   - pgAdmin: https://www.pgadmin.org/")
        print("   - Command line: psql -U postgres -d sentinel_db")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is installed and running")
        print("  2. The database exists (create it with: CREATE DATABASE sentinel_db;)")
        print("  3. DATABASE_URL environment variable is set correctly")
        print("  4. You have the correct credentials (username, password)")
        print("\nExample DATABASE_URL:")
        print("  postgresql://username:password@localhost:5432/sentinel_db")
        sys.exit(1)
