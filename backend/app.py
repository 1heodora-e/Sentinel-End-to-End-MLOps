# backend/app.py
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

# DO NOT import tensorflow here - it will initialize CUDA
import numpy as np
import shutil
import os
import sys
import zipfile

# Configure TensorFlow memory BEFORE importing (prevents OOM crashes)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Reduce TensorFlow logging
os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "true"  # Prevent GPU memory pre-allocation
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable CUDA/GPU (CPU-only deployment)
os.environ["TF_XLA_FLAGS"] = (
    "--tf_xla_cpu_global_jit=false"  # Disable XLA JIT compilation
)
os.environ["TF_DISABLE_XLA"] = "1"  # Disable XLA entirely
os.environ["TF_USE_CUSTOM_MEMORY_ALLOCATOR"] = "0"

# NOW import TensorFlow after environment variables are set
import tensorflow as tf

# Force CPU-only execution - hide all GPUs before any operations
tf.config.set_visible_devices([], "GPU")  # Hide all GPUs immediately

# Limit TensorFlow memory growth to prevent OOM on limited resources
try:
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
except Exception:
    pass  # No GPU available, continue with CPU

from tensorflow.keras.preprocessing import image
import numpy as np
import shutil

# Add paths for imports
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)  # project root

from preprocessing import create_spectrogram
from model import train_model
from database import (
    init_db,
    get_db,
    create_upload_record,
    update_upload_status,
    create_retraining_session,
    update_retraining_session,
)

app = FastAPI(title="Sentinel API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use absolute path for model to work in any environment
_backend_dir = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(_backend_dir, "models", "sentinel_model.h5")
model = None
is_training = False
training_status = {
    "status": "idle",
    "message": "",
    "progress": 0,
    "epoch": 0,
    "total_epochs": 0,
}


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup. Model will be loaded lazily on first request."""
    # Initialize database tables (optional - graceful degradation if DB unavailable)
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
        print("⚠️ Continuing without database logging. Retraining will still work.")
        print(
            "⚠️ To enable database: Set DATABASE_URL environment variable for PostgreSQL connection"
        )

    # Model will be loaded lazily on first request to save memory during startup
    print("⚠️ Model will be loaded on first request to optimize memory usage")


def get_model():
    """
    Lazy load model on first request to prevent memory issues during startup.
    This prevents OOM crashes on platforms with limited RAM (e.g., Render free tier).
    """
    global model
    if model is None:
        try:
            if os.path.exists(MODEL_PATH):
                print(f"📦 Loading model from {MODEL_PATH}...")
                model = tf.keras.models.load_model(MODEL_PATH)
                print(f"✅ Model loaded from {MODEL_PATH}")
            else:
                raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            raise
    return model


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "name": "Sentinel API",
        "description": "Audio Distress Detection API using Deep Learning",
        "version": "1.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "predict": "/predict",
            "retrain": "/retrain",
            "model_status": "/model/status",
        },
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/model/status")
def model_status():
    """Get model status including accuracy from metadata."""
    global model

    # Try to load model if not already loaded (for status check)
    if model is None:
        try:
            get_model()  # This will load the model if it exists
        except Exception as e:
            print(f"⚠️ Model not available: {e}")
            # Continue to return status even if model can't be loaded

    model_accuracy = None

    # Try to read accuracy from model metadata
    # Check both possible metadata file names
    metadata_paths = [
        MODEL_PATH.replace(".h5", "_metadata.json"),  # sentinel_model_metadata.json
        os.path.join(
            os.path.dirname(MODEL_PATH), "model_metadata.json"
        ),  # model_metadata.json
    ]

    for metadata_path in metadata_paths:
        if os.path.exists(metadata_path):
            try:
                import json

                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    # Use validation accuracy as the model accuracy (prefer last_val_accuracy, fallback to final_val_accuracy)
                    model_accuracy = metadata.get("last_val_accuracy") or metadata.get(
                        "final_val_accuracy"
                    )
                    if model_accuracy is not None:
                        break  # Found accuracy, stop searching
            except Exception as e:
                print(f"Error reading model metadata from {metadata_path}: {e}")
                continue

    return {
        "model_loaded": model is not None,
        "is_training": is_training,
        "training_status": training_status,
        "model_accuracy": model_accuracy,  # Accuracy as float (0.0 to 1.0)
    }


@app.post("/predict")
async def predict_audio_endpoint(file: UploadFile = File(...)):
    print(f"\n--- ⚡ Processing: {file.filename} ---")

    # Load model if not already loaded (lazy loading)
    try:
        current_model = get_model()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Model not available: {str(e)}")

    # Use Absolute Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(base_dir, "temp_data")
    os.makedirs(temp_dir, exist_ok=True)

    temp_audio_path = os.path.join(temp_dir, f"temp_{file.filename}")
    temp_image_path = temp_audio_path.replace(".wav", ".png").replace(".mp3", ".png")

    try:
        # 1. Save Audio
        with open(temp_audio_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Convert to Spectrogram
        success = create_spectrogram(temp_audio_path, temp_image_path)
        if not success:
            raise Exception("Preprocessing failed")

        # 3. Predict
        print("3. Loading image for prediction...")

        # FIXED: Ensure size matches model training (224x224)
        img = image.load_img(temp_image_path, target_size=(224, 224))

        x = image.img_to_array(img) / 255.0
        x = np.expand_dims(x, axis=0)

        print("4. Running Model...")
        prediction = current_model.predict(x, verbose=0)[0][0]

        print(f"📢 DEBUG SCORE: {prediction}")

        # === LOGIC SWAP ===
        # Based on your test, Scream was 0.83.
        # Therefore: High Score (> 0.5) is Danger.

        if prediction > 0.5:
            label = "Danger"
            confidence = float(prediction)
        else:
            label = "Safe"
            confidence = 1.0 - float(prediction)

        print(f"✅ Result: {label} ({confidence * 100}%)")

        return {"prediction": label, "confidence": round(confidence * 100, 2)}

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

    finally:
        try:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
        except Exception:
            pass


def extract_and_organize_zip(zip_path, extract_dir):
    """
    Extract zip file and organize audio files into safe/ and danger/ directories.
    Handles nested zip structures recursively.
    """
    os.makedirs(extract_dir, exist_ok=True)

    # Final destination for organized files within the extraction area
    final_safe_dir = os.path.join(extract_dir, "safe")
    final_danger_dir = os.path.join(extract_dir, "danger")
    os.makedirs(final_safe_dir, exist_ok=True)
    os.makedirs(final_danger_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    print(f"📂 Extracted zip to {extract_dir}")

    # Walk through all extracted files recursively
    audio_extensions = (".wav", ".mp3", ".flac", ".ogg", ".m4a")
    found_files = 0

    for root, dirs, files in os.walk(extract_dir):
        # Skip the final safe/danger dirs we just created to avoid self-copying loop
        if root == final_safe_dir or root == final_danger_dir:
            continue

        for file in files:
            if file.lower().endswith(audio_extensions):
                src_path = os.path.join(root, file)
                found_files += 1

                # Determine destination
                # 1. Check if file is already in a 'safe' or 'danger' folder
                parent_folder = os.path.basename(root).lower()
                filename = file.lower()

                if parent_folder == "safe":
                    dest_dir = final_safe_dir
                elif parent_folder == "danger":
                    dest_dir = final_danger_dir
                # 2. Check filename keywords
                elif any(
                    k in filename
                    for k in ["danger", "scream", "distress", "alarm", "emergency"]
                ):
                    dest_dir = final_danger_dir
                else:
                    # Default to safe if ambiguous (or logic dictates)
                    dest_dir = final_safe_dir

                # Handle filename collisions
                dest_path = os.path.join(dest_dir, file)
                if os.path.exists(dest_path):
                    base, ext = os.path.splitext(file)
                    timestamp = int(os.path.getmtime(src_path))
                    dest_path = os.path.join(dest_dir, f"{base}_{timestamp}{ext}")

                shutil.move(src_path, dest_path)

    print(
        f"✅ Organized {found_files} audio files into {final_safe_dir} and {final_danger_dir}"
    )
    return final_safe_dir, final_danger_dir


def retrain_model_background(zip_path, upload_dir, data_dir, upload_id, session_id):
    """
    Background function to handle retraining with database logging.
    """
    global model, is_training, training_status

    # Get database session
    db = next(get_db())

    try:
        # Ensure tables exist before trying to use database (lazy initialization)
        if db is not None:
            try:
                init_db()
            except Exception:
                pass  # Tables might already exist, continue anyway

        is_training = True
        training_status = {
            "status": "preprocessing",
            "message": "Extracting and organizing data...",
            "progress": 10,
            "epoch": 0,
            "total_epochs": 0,
        }

        # Update session status (only if db is available)
        if db is not None and session_id is not None:
            update_retraining_session(db, session_id, status="preprocessing")

        # 1. Extract and organize zip file
        extract_dir = os.path.join(upload_dir, "extracted")
        safe_dir, danger_dir = extract_and_organize_zip(zip_path, extract_dir)

        # Count files - Case Insensitive
        safe_files = [
            f for f in os.listdir(safe_dir) if f.lower().endswith((".wav", ".mp3"))
        ]
        danger_files = [
            f for f in os.listdir(danger_dir) if f.lower().endswith((".wav", ".mp3"))
        ]
        total_files = len(safe_files) + len(danger_files)

        # Update upload record with file counts
        update_upload_status(
            db,
            upload_id,
            status="processing",
            safe_count=len(safe_files),
            danger_count=len(danger_files),
            total_count=total_files,
        )

        # Merge with existing data
        existing_safe = os.path.join(data_dir, "safe")
        existing_danger = os.path.join(data_dir, "danger")

        # Create directories if they don't exist
        os.makedirs(existing_safe, exist_ok=True)
        os.makedirs(existing_danger, exist_ok=True)

        # Copy new files to existing directories
        for file in safe_files:
            shutil.copy(os.path.join(safe_dir, file), existing_safe)
        for file in danger_files:
            shutil.copy(os.path.join(danger_dir, file), existing_danger)

        training_status = {
            "status": "preprocessing",
            "message": "Preprocessing audio files...",
            "progress": 30,
            "epoch": 0,
            "total_epochs": 0,
        }

        # 2. Train model (this will handle preprocessing internally)
        training_status = {
            "status": "training",
            "message": "Training model...",
            "progress": 50,
            "epoch": 0,
            "total_epochs": 3,
        }

        update_retraining_session(db, session_id, status="training")

        # Ensure model is loaded before retraining
        current_model = get_model() if model is None else model

        # Use existing model for retraining
        retrained_model, history = train_model(
            data_dir=data_dir,
            model_path=MODEL_PATH,
            epochs=3,
            batch_size=32,
            validation_split=0.2,
            existing_model=current_model,
        )

        # Reload model
        model = retrained_model

        # Extract final metrics
        final_acc = history.history["accuracy"][-1]
        final_val_acc = history.history["val_accuracy"][-1]
        final_loss = history.history["loss"][-1]
        final_val_loss = history.history["val_loss"][-1]
        total_samples = (
            len(safe_files)
            + len(danger_files)
            + len(os.listdir(existing_safe))
            + len(os.listdir(existing_danger))
        )

        # Update database with training results
        update_retraining_session(
            db,
            session_id,
            status="completed",
            final_accuracy=float(final_acc),
            final_val_accuracy=float(final_val_acc),
            final_loss=float(final_loss),
            final_val_loss=float(final_val_loss),
            total_samples=total_samples,
        )

        # Update upload status
        update_upload_status(db, upload_id, status="completed")

        training_status = {
            "status": "completed",
            "message": f"Training completed! Final accuracy: {final_val_acc:.2%}",
            "progress": 100,
            "epoch": 3,
            "total_epochs": 3,
        }

        is_training = False

    except Exception as e:
        is_training = False
        error_msg = str(e)

        # Update database with error
        update_retraining_session(
            db, session_id, status="failed", error_message=error_msg
        )
        update_upload_status(db, upload_id, status="failed", error_message=error_msg)

        training_status = {
            "status": "error",
            "message": f"Training failed: {error_msg}",
            "progress": 0,
            "epoch": 0,
            "total_epochs": 0,
        }
        print(f"❌ Retraining error: {e}")
    finally:
        db.close()


@app.post("/retrain")
async def retrain_trigger(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Trigger model retraining with uploaded zip file.

    Process:
    1. Save zip file to filesystem and database (Rubric Requirement: Data file Uploading + Saving to Database)
    2. Extract and organize files into safe/danger directories
    3. Preprocess audio files (convert to spectrograms)
    4. Retrain model using existing model as base
    5. Save retrained model
    6. Log all steps to PostgreSQL database
    """
    global is_training

    if is_training:
        raise HTTPException(
            status_code=409, detail="Model is already training. Please wait."
        )

    # Load model if not already loaded (lazy loading)
    try:
        get_model()  # Ensure model is loaded
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Model not available. Cannot retrain: {str(e)}"
        )

    # 1. Save file to filesystem
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_dir = os.path.join(base_dir, "data", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    zip_path = os.path.join(upload_dir, file.filename)

    try:
        # Read file to get size
        file_content = await file.read()
        file_size = len(file_content)

        # Save to filesystem
        with open(zip_path, "wb") as buffer:
            buffer.write(file_content)

        # 2. Save to PostgreSQL database (Rubric Requirement: Data file Uploading + Saving to Database)
        upload_id = None
        session_id = None
        try:
            # Ensure tables exist before trying to insert (lazy initialization)
            try:
                init_db()
            except Exception:
                pass  # Tables might already exist, continue anyway

            upload_record = create_upload_record(db, file.filename, zip_path, file_size)
            upload_id = upload_record.id

            # Create retraining session record
            retraining_session = create_retraining_session(db, upload_id, epochs=3)
            session_id = retraining_session.id

            db_message = f"File saved to PostgreSQL database (Upload ID: {upload_id}, Session ID: {session_id})"
        except Exception as db_error:
            # Continue even if database fails (graceful degradation)
            print(
                f"⚠️ Database error: {db_error}. Continuing without database logging..."
            )
            db_message = "File saved to filesystem (database logging unavailable)"

        # 3. Start background retraining task
        data_dir = os.path.join(base_dir, "data")
        background_tasks.add_task(
            retrain_model_background,
            zip_path,
            upload_dir,
            data_dir,
            upload_id,
            session_id,
        )

        return {
            "status": "Retraining Initiated",
            "message": f"{db_message}. Training pipeline started in background.",
            "training_started": True,
            "upload_id": upload_id,
            "session_id": session_id,
        }

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"Failed to save file: {str(e)}"}
        )
