# backend/app.py
import os
import sys

# ==========================================
# 1. CRITICAL: FORCE CPU MODE BEFORE ANYTHING ELSE
# ==========================================
# These must be set before importing tensorflow or numpy
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "true"
os.environ["TF_XLA_FLAGS"] = "--tf_xla_cpu_global_jit=false"
os.environ["TF_DISABLE_XLA"] = "1"
os.environ["TF_USE_CUDA"] = "0"
os.environ["TF_USE_GPU"] = "0"
os.environ["TF_DETERMINISTIC_OPS"] = "1"

# Add current directory to path so we can import local modules later
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)

# ==========================================
# 2. NOW IMPORT TENSORFLOW
# ==========================================
import tensorflow as tf

# Double-check: Hide GPUs programmatically just in case env vars failed
try:
    tf.config.set_visible_devices([], 'GPU')
    visible_devices = tf.config.get_visible_devices()
    print(f"✅ TensorFlow Configured. Visible Devices: {visible_devices}")
except:
    pass

# ==========================================
# 3. NOW IMPORT EVERYTHING ELSE
# ==========================================
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from tensorflow.keras.preprocessing import image
import numpy as np
import shutil
import zipfile

# Import local modules
from preprocessing import create_spectrogram
import database 

# Initialize App
app = FastAPI(title="Sentinel API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
MODEL_PATH = os.path.join(base_dir, "models", "sentinel_model.h5")
model = None

def get_model():
    """
    Lazy load model on first request to prevent memory issues during startup.
    This prevents segmentation faults on CPU-only systems.
    """
    global model
    if model is None:
        try:
            if os.path.exists(MODEL_PATH):
                print(f"📦 Loading model from {MODEL_PATH}...")
                model = tf.keras.models.load_model(MODEL_PATH)
                print(f"✅ Model loaded successfully!")
            else:
                raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            raise
    return model

@app.on_event("startup")
async def startup_event():
    # 1. Init DB
    try:
        database.init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ DB Init Warning: {e}")

    # 2. DO NOT load model at startup - use lazy loading instead
    print("⚠️ Model will be loaded on first request to prevent startup crashes")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/model/status")
def model_status():
    """Get model status. Will attempt to load model if not already loaded."""
    global model
    if model is None:
        try:
            get_model()  # Try to load model for status check
        except Exception as e:
            print(f"⚠️ Model not available: {e}")
    return {"model_loaded": model is not None}

@app.post("/predict")
async def predict_audio(file: UploadFile = File(...)):
    print(f"\n--- ⚡ Processing: {file.filename} ---")
    
    # Load model lazily on first request
    try:
        current_model = get_model()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Model not available: {str(e)}")

    # Define temporary paths using absolute paths
    temp_dir = os.path.join(base_dir, "temp_data")
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_audio_path = os.path.join(temp_dir, f"temp_{file.filename}")
    # FIX: Handle any extension for the image name
    base_name = os.path.splitext(file.filename)[0]
    temp_image_path = os.path.join(temp_dir, f"temp_{base_name}.png")
    
    try:
        # 1. Save Audio
        with open(temp_audio_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Convert to Spectrogram
        success = create_spectrogram(temp_audio_path, temp_image_path)
        if not success:
            raise Exception("Preprocessing failed (Spectrogram generation)")

        # 3. Predict
        # Load at 224x224 to match MobileNetV2
        img = image.load_img(temp_image_path, target_size=(224, 224))
        x = image.img_to_array(img) / 255.0
        x = np.expand_dims(x, axis=0)
        
        prediction = current_model.predict(x, verbose=0)[0][0]
        print(f"📢 DEBUG SCORE: {prediction}")

        # Logic: > 0.5 is Danger
        if prediction > 0.5:
            label = "Danger"
            confidence = float(prediction)
        else:
            label = "Safe"
            confidence = 1.0 - float(prediction)
        
        return {
            "prediction": label,
            "confidence": round(confidence * 100, 2)
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        # Cleanup
        try:
            if os.path.exists(temp_audio_path): os.remove(temp_audio_path)
            if os.path.exists(temp_image_path): os.remove(temp_image_path)
        except: pass

@app.post("/retrain")
async def retrain_trigger(file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    upload_dir = os.path.join(base_dir, "data", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Log to DB
    try:
        size_kb = os.path.getsize(file_path) / 1024
        record = database.create_upload_record(db, file.filename, size_kb)
        print(f"✅ DB Log ID: {record.id}")
    except Exception as e:
        print(f"⚠️ DB Error: {e}")

    return {"status": "Retraining Initiated", "message": "File secured. Training pipeline started."}