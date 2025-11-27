# backend/database.py
"""
Database models and connection for PostgreSQL.
Stores training data uploads and retraining history.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Try to load from .env file if available
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use environment variables only

# PostgreSQL connection string
# Format: postgresql+pg8000://username:password@host:port/database
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+pg8000://postgres:postgres@localhost:5432/sentinel_db"
)

# Ensure we use pg8000 driver even if env var specifies default postgresql://
if (
    DATABASE_URL
    and "postgresql://" in DATABASE_URL
    and "postgresql+pg8000://" not in DATABASE_URL
):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://")

# Engine and session factory - created lazily to avoid memory conflicts at import time
_engine = None
_SessionLocal = None


def _get_engine():
    """Get or create database engine (lazy initialization)."""
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(
            DATABASE_URL,
            pool_size=5,  # Limit connection pool size
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=False,  # Don't echo SQL queries
        )
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_session_local():
    """Get session factory (creates engine if needed)."""
    if _SessionLocal is None:
        _get_engine()
    return _SessionLocal


# Base class for models
Base = declarative_base()


class TrainingDataUpload(Base):
    """Model for storing training data uploads."""

    __tablename__ = "training_data_uploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(
        String(50), default="pending"
    )  # pending, processing, completed, failed
    safe_count = Column(Integer, default=0)
    danger_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)


class RetrainingSession(Base):
    """Model for storing retraining session information."""

    __tablename__ = "retraining_sessions"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, nullable=False)  # Foreign key to training_data_uploads
    start_timestamp = Column(DateTime, default=datetime.utcnow)
    end_timestamp = Column(DateTime, nullable=True)
    status = Column(
        String(50), default="pending"
    )  # pending, preprocessing, training, completed, failed
    epochs = Column(Integer, default=10)
    final_accuracy = Column(Float, nullable=True)
    final_val_accuracy = Column(Float, nullable=True)
    final_loss = Column(Float, nullable=True)
    final_val_loss = Column(Float, nullable=True)
    total_samples = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)


def init_db():
    """Initialize database tables."""
    try:
        engine = _get_engine()
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        print(
            f"📊 Database: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}"
        )
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        print("\n💡 Make sure PostgreSQL is running and DATABASE_URL is correct.")
        raise


def get_db():
    """Dependency for getting database session."""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Helper functions for database operations
def create_upload_record(db, filename, file_path, file_size):
    """Create a new upload record."""
    upload = TrainingDataUpload(
        filename=filename, file_path=file_path, file_size=file_size, status="pending"
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def update_upload_status(
    db, upload_id, status=None, safe_count=None, danger_count=None, total_count=None
):
    """Update upload status and counts."""
    upload = (
        db.query(TrainingDataUpload).filter(TrainingDataUpload.id == upload_id).first()
    )
    if upload:
        if status:
            upload.status = status
        if safe_count is not None:
            upload.safe_count = safe_count
        if danger_count is not None:
            upload.danger_count = danger_count
        if total_count is not None:
            upload.total_count = total_count
        db.commit()
        db.refresh(upload)
    return upload


def create_retraining_session(db, upload_id, epochs=10):
    """Create a new retraining session."""
    session = RetrainingSession(upload_id=upload_id, epochs=epochs, status="pending")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def update_retraining_session(
    db,
    session_id,
    status=None,
    final_accuracy=None,
    final_val_accuracy=None,
    final_loss=None,
    final_val_loss=None,
    total_samples=None,
    error_message=None,
):
    """Update retraining session with results."""
    session = (
        db.query(RetrainingSession).filter(RetrainingSession.id == session_id).first()
    )
    if session:
        if status:
            session.status = status
        if final_accuracy is not None:
            session.final_accuracy = final_accuracy
        if final_val_accuracy is not None:
            session.final_val_accuracy = final_val_accuracy
        if final_loss is not None:
            session.final_loss = final_loss
        if final_val_loss is not None:
            session.final_val_loss = final_val_loss
        if total_samples is not None:
            session.total_samples = total_samples
        if error_message:
            session.error_message = error_message
        if status == "completed" or status == "failed":
            session.end_timestamp = datetime.utcnow()
        db.commit()
        db.refresh(session)
    return session
