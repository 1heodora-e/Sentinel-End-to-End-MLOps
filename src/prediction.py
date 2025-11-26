# src/prediction.py
"""
Prediction functions for Sentinel audio classification.
"""
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import sys
import os

# Add parent directory to path to import preprocessing
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.preprocessing import create_spectrogram

def predict_audio(model, audio_path):
    """
    Make prediction on a single audio file.
    
    Args:
        model: Trained Keras model
        audio_path: Path to audio file
    
    Returns:
        dict with 'prediction' (0 or 1), 'class' (str), 'confidence' (float), 'probability' (float)
    """
    import tempfile
    
    # Create temporary spectrogram
    temp_dir = os.path.join(os.path.dirname(audio_path), "temp_predict")
    os.makedirs(temp_dir, exist_ok=True)
    temp_img_path = os.path.join(temp_dir, "temp_spec.png")
    
    try:
        # Process audio to spectrogram
        success = create_spectrogram(audio_path, temp_img_path)
        if not success:
            raise Exception("Failed to create spectrogram")
        
        # Load and preprocess image
        img = image.load_img(temp_img_path, target_size=(224, 224))
        img_array = image.img_to_array(img) / 255.0
        img_batch = np.expand_dims(img_array, axis=0)
        
        # Predict
        prediction = model.predict(img_batch, verbose=0)[0][0]
        
        # Binary classification: 0 = Safe, 1 = Danger
        class_idx = 1 if prediction > 0.5 else 0
        confidence = abs(prediction - 0.5) * 2  # Convert to [0, 1] confidence
        
        return {
            'prediction': int(class_idx),
            'class': 'danger' if class_idx == 1 else 'safe',
            'confidence': float(confidence),
            'probability': float(prediction)  # Raw probability (0=Safe, 1=Danger)
        }
    finally:
        # Clean up temp file
        try:
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
        except:
            pass

def predict_batch(model, audio_paths):
    """
    Make predictions on multiple audio files.
    
    Args:
        model: Trained Keras model
        audio_paths: List of paths to audio files
    
    Returns:
        List of prediction dictionaries
    """
    results = []
    for audio_path in audio_paths:
        try:
            result = predict_audio(model, audio_path)
            results.append(result)
        except Exception as e:
            print(f"Error predicting {audio_path}: {e}")
            results.append(None)
    return results

