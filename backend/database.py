# backend/database.py
"""
Database models and connection for SQLite.
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

# SQLite database path - creates a file in the backend directory
# You can change this path if you want the database elsewhere
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "sentinel.db")

# SQLite connection string (file-based, no server needed!)
# sqlite:/// means SQLite, and the path is relative or absolute
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Create engine with SQLite-specific settings
# check_same_thread=False allows SQLite to work with FastAPI's async nature
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class TrainingDataUpload(Base):
    """Model for storing training data uploads."""

    __tablename__ = "training_data_uploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # Size in bytes
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(
        String(50), default="uploaded"
    )  # uploaded, processing, completed, failed
    safe_files_count = Column(Integer, default=0)
    danger_files_count = Column(Integer, default=0)
    total_files_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)


class RetrainingSession(Base):
    """Model for storing retraining session history."""

    __tablename__ = "retraining_sessions"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, nullable=False)  # Foreign key to TrainingDataUpload
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(
        String(50), default="started"
    )  # started, preprocessing, training, completed, failed
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
        Base.metadata.create_all(bind=engine)
        print(f"✅ Database initialized at: {DB_PATH}")
    except Exception as e:
        print(f"⚠️ Database initialization error: {e}")
        raise


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_upload_record(db, filename, file_path, file_size):
    """Create a new training data upload record."""
    upload = TrainingDataUpload(
        filename=filename, file_path=file_path, file_size=file_size, status="uploaded"
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def update_upload_status(
    db, upload_id, status, safe_count=0, danger_count=0, total_count=0, error=None
):
    """Update upload status and file counts."""
    upload = (
        db.query(TrainingDataUpload).filter(TrainingDataUpload.id == upload_id).first()
    )
    if upload:
        upload.status = status
        upload.safe_files_count = safe_count
        upload.danger_files_count = danger_count
        upload.total_files_count = total_count
        if error:
            upload.error_message = error
        db.commit()
        return upload
    return None


def create_retraining_session(db, upload_id, epochs=10):
    """Create a new retraining session record."""
    session = RetrainingSession(upload_id=upload_id, status="started", epochs=epochs)
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
    error=None,
):
    """Update retraining session status and metrics."""
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
        if error:
            session.error_message = error
        if status == "completed" or status == "failed":
            session.end_time = datetime.utcnow()
        db.commit()
        return session
    return None
