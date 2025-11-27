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


if __name__ == "__main__":
    print("Preprocessing module ready.")
