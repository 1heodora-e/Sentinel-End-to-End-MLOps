# src/model.py
"""
Model architecture and training functions for Sentinel audio classification.
"""

import os
import sys
import json
from pathlib import Path

# Configure TensorFlow for CPU-only BEFORE importing TensorFlow
# This prevents CUDA initialization errors on CPU-only systems (e.g., Render)
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_FORCE_GPU_ALLOW_GROWTH", "true")
os.environ.setdefault("TF_XLA_FLAGS", "--tf_xla_cpu_global_jit=false")
os.environ.setdefault("TF_DISABLE_XLA", "1")

import numpy as np
import tensorflow as tf

# Force CPU-only execution immediately after import
try:
    tf.config.set_visible_devices([], "GPU")
    # Enable eager execution to fix "numpy() is only available when eager execution is enabled" error
    tf.config.run_functions_eagerly(True)
except Exception:
    pass  # Ignore if already configured

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.preprocessing import image

# Add parent directory to path to import preprocessing
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Import preprocessing from backend directory
from backend.preprocessing import create_spectrogram

# Configuration
INPUT_SHAPE = (224, 224, 3)


def create_model(input_shape=INPUT_SHAPE, num_classes=2, weights=None):
    """
    Create MobileNetV2-based model for binary audio classification.

    Args:
        input_shape: Input image shape (default: (224, 224, 3))
        num_classes: Number of output classes (default: 2 for binary)
        weights: Path to pretrained weights or None for random init

    Returns:
        Compiled Keras model
    """
    # Base MobileNetV2 (pretrained on ImageNet, excluding top)
    base_model = MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights="imagenet" if weights is None else None,
        alpha=1.0,
    )

    # Freeze base model initially (can be unfrozen during fine-tuning)
    base_model.trainable = False

    # Build custom classifier head
    inputs = keras.Input(shape=input_shape)

    # Preprocess for MobileNetV2
    x = base_model(inputs, training=False)

    # Global average pooling
    x = layers.GlobalAveragePooling2D()(x)

    # Dense layers with regularization
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.5)(x)  # Regularization
    x = layers.Dense(64, activation="relu")(x)
    x = layers.Dropout(0.3)(x)  # Regularization

    # Output layer (binary classification)
    if num_classes == 2:
        outputs = layers.Dense(1, activation="sigmoid", name="predictions")(x)
        loss = "binary_crossentropy"
    else:
        outputs = layers.Dense(num_classes, activation="softmax", name="predictions")(x)
        loss = "sparse_categorical_crossentropy"

    model = keras.Model(inputs, outputs, name="sentinel_mobilenet")

    # Compile model with optimizer
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss=loss,
        metrics=["accuracy"],
    )

    return model


def load_model(model_path):
    """
    Load trained model from disk.

    Args:
        model_path: Path to saved model file

    Returns:
        Loaded Keras model, or None if file doesn't exist
    """
    if os.path.exists(model_path):
        try:
            model = keras.models.load_model(model_path)
            return model
        except Exception as e:
            print(f"Error loading model: {e}")
            return None
    return None


def save_model(model, model_path, metadata=None):
    """
    Save model and optional metadata to disk.

    Args:
        model: Keras model to save
        model_path: Path to save model
        metadata: Optional dictionary of metadata to save
    """
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.save(model_path)

    if metadata:
        metadata_path = model_path.replace(".h5", "_metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)


def prepare_data_from_directories(data_dir, validation_split=0.2):
    """
    Prepare training data from directory structure:
    data_dir/
        safe/
            audio1.wav
            audio2.wav
        danger/
            audio1.wav
            audio2.wav

    Args:
        data_dir: Root directory containing class subdirectories
        validation_split: Fraction of data to use for validation

    Returns:
        train_generator, val_generator, num_samples
    """
    data_path = Path(data_dir)
    safe_dir = data_path / "safe"
    danger_dir = data_path / "danger"

    # Collect all audio files - Case Insensitive
    extensions = ["*.wav", "*.WAV", "*.mp3", "*.MP3"]
    safe_files = []
    danger_files = []

    for ext in extensions:
        safe_files.extend(list(safe_dir.glob(ext)))
        danger_files.extend(list(danger_dir.glob(ext)))

    if len(safe_files) == 0 and len(danger_files) == 0:
        raise ValueError(f"No audio files found in {data_dir}")

    # Process audio files to images
    X = []
    y = []

    # Create temp directory for spectrograms
    temp_spec_dir = data_path / "temp_spectrograms"
    temp_spec_dir.mkdir(exist_ok=True)

    print(
        f"Processing {len(safe_files)} safe files and {len(danger_files)} danger files..."
    )

    for file_path in safe_files:
        try:
            # Create temporary spectrogram
            temp_img = temp_spec_dir / f"{file_path.stem}.png"

            if create_spectrogram(str(file_path), str(temp_img)):
                img = image.load_img(str(temp_img), target_size=(224, 224))
                img_array = image.img_to_array(img) / 255.0
                X.append(img_array)
                y.append(0)  # Safe class
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue

    for file_path in danger_files:
        try:
            temp_img = temp_spec_dir / f"{file_path.stem}.png"

            if create_spectrogram(str(file_path), str(temp_img)):
                img = image.load_img(str(temp_img), target_size=(224, 224))
                img_array = image.img_to_array(img) / 255.0
                X.append(img_array)
                y.append(1)  # Danger class
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue

    if len(X) == 0:
        raise ValueError("No valid audio files could be processed")

    # Convert to numpy arrays
    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.float32)

    # Shuffle data
    indices = np.random.permutation(len(X))
    X = X[indices]
    y = y[indices]

    # Split into train/validation
    split_idx = int(len(X) * (1 - validation_split))
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]

    # Apply data augmentation
    datagen = ImageDataGenerator(
        rotation_range=5,
        width_shift_range=0.1,
        height_shift_range=0.1,
        zoom_range=0.1,
        horizontal_flip=False,  # Don't flip spectrograms
        fill_mode="nearest",
    )

    train_generator = datagen.flow(X_train, y_train, batch_size=32, shuffle=True)
    val_generator = datagen.flow(X_val, y_val, batch_size=32, shuffle=False)

    num_samples = len(X)

    return train_generator, val_generator, num_samples


def train_model(
    data_dir,
    model_path,
    epochs=10,
    batch_size=32,
    validation_split=0.2,
    existing_model=None,
):
    """
    Train the Sentinel model on audio data.

    Args:
        data_dir: Directory containing safe/ and danger/ subdirectories
        model_path: Path to save model
        epochs: Number of training epochs
        batch_size: Batch size for training
        validation_split: Fraction of data for validation
        existing_model: Existing model to continue training, or None to create new

    Returns:
        Trained model and training history
    """
    # Load or create model
    if existing_model is not None:
        model = existing_model
        print("Using provided model for retraining...")
    elif os.path.exists(model_path):
        print(f"Loading existing model from {model_path}...")
        model = load_model(model_path)
        if model is None:
            print("Failed to load model, creating new one...")
            model = create_model()
    else:
        print("Creating new model...")
        model = create_model()

    # Prepare data
    print(f"Loading data from {data_dir}...")
    train_gen, val_gen, num_samples = prepare_data_from_directories(
        data_dir, validation_split=validation_split
    )

    print(f"Training on {num_samples} samples...")

    # Callbacks with optimization techniques
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=5, restore_best_weights=True, verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=3, min_lr=1e-7, verbose=1
        ),
    ]

    # Train model
    history = model.fit(
        train_gen,
        epochs=epochs,
        validation_data=val_gen,
        callbacks=callbacks,
        verbose=1,
    )

    # Save model
    metadata = {
        "epochs_trained": epochs,
        "total_samples": num_samples,
        "last_accuracy": float(history.history["accuracy"][-1]),
        "last_val_accuracy": float(history.history["val_accuracy"][-1]),
        "last_loss": float(history.history["loss"][-1]),
        "last_val_loss": float(history.history["val_loss"][-1]),
    }

    save_model(model, model_path, metadata=metadata)

    print("Model training completed and saved!")

    return model, history
