# src/preprocessing.py
import os
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend (fixes tkinter errors)
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np

# Settings - UPDATED TO MATCH MODEL INPUT (224x224)
IMG_SIZE = (224, 224)
SAMPLE_RATE = 22050
DURATION = 3.0


def create_spectrogram(audio_path, save_path):
    """
    Convert audio file to mel spectrogram image.

    Args:
        audio_path: Path to input audio file
        save_path: Path to save spectrogram image

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # 1. Load Audio
        y, sr = librosa.load(audio_path, sr=SAMPLE_RATE, duration=DURATION)

        # 2. Pad/Truncate
        target_length = int(SAMPLE_RATE * DURATION)
        if len(y) < target_length:
            y = np.pad(y, (0, target_length - len(y)))
        else:
            y = y[:target_length]

        # 3. Mel Spectrogram
        # Increased n_mels to ensure we have enough pixel density for 224x224
        mel_spectrogram = librosa.feature.melspectrogram(
            y=y, sr=sr, n_mels=128, fmax=8000
        )
        mel_spectrogram_db = librosa.power_to_db(mel_spectrogram, ref=np.max)

        # 4. Save Image (No axes)
        # 4x4 inches at default DPI (100) = 400x400 pixels.
        # This is safely larger than 224x224, so resizing later won't lose quality.
        plt.figure(figsize=(4, 4))
        librosa.display.specshow(mel_spectrogram_db, sr=sr, fmax=8000)
        plt.axis("off")

        # --- THE FIX FOR WIN ERROR 3 ---
        directory = os.path.dirname(save_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        # -------------------------------

        plt.savefig(save_path, bbox_inches="tight", pad_inches=0)
        plt.close()
        return True

    except Exception as e:
        print(f"Error in preprocessing: {e}")
        return False


def audio_file_to_image(audio_path):
    """
    Convert audio file to PIL Image (in-memory).

    Args:
        audio_path: Path to input audio file

    Returns:
        PIL Image object ready for model input
    """
    import tempfile
    import time
    from PIL import Image
    import io

    # Use system temp directory instead of data directory to avoid conflicts
    temp_dir = tempfile.gettempdir()
    os.makedirs(temp_dir, exist_ok=True)
    # Use unique filename with timestamp and process ID to avoid conflicts
    import hashlib

    unique_id = hashlib.md5(
        f"{time.time()}_{os.getpid()}_{audio_path}".encode()
    ).hexdigest()[:8]
    temp_file = os.path.join(temp_dir, f"sentinel_spec_{unique_id}.png")

    try:
        # Create spectrogram
        if create_spectrogram(audio_path, temp_file):
            # Read file into BytesIO buffer first (closes file handle immediately)
            with open(temp_file, "rb") as f:
                image_data = f.read()

            # Now we can delete the file since we have the data in memory
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except (PermissionError, OSError):
                pass  # Ignore cleanup errors on Windows

            # Load image from bytes and ensure RGB mode (3 channels)
            img = Image.open(io.BytesIO(image_data))
            # Convert to RGB if not already (handles RGBA, grayscale, etc.)
            if img.mode != "RGB":
                img = img.convert("RGB")
            return img
        else:
            raise Exception("Failed to create spectrogram")
    except Exception as e:
        # Clean up on error
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except (PermissionError, OSError):
            pass  # Ignore cleanup errors
        raise e


def image_to_array(img):
    """
    Convert PIL Image to numpy array normalized for model input.

    Args:
        img: PIL Image object

    Returns:
        numpy array with shape (224, 224, 3) normalized to [0, 1]
    """
    from tensorflow.keras.preprocessing import image as keras_image

    # Ensure image is RGB mode (3 channels) - convert from RGBA/grayscale/etc to RGB
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Resize to model input size
    img = img.resize((224, 224))

    # Convert to array and normalize
    img_array = keras_image.img_to_array(img) / 255.0

    return img_array


if __name__ == "__main__":
    print("Preprocessing module ready.")
