"""
Locust file for flood testing the Sentinel API.
Run with: locust -f locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between
import random
import os
from pathlib import Path


class SentinelUser(HttpUser):
    """Simulate user behavior for load testing."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a simulated user starts."""
        # Check health endpoint first
        self.client.get("/health")
    
    @task(3)
    def check_health(self):
        """Check API health (most common operation)."""
        self.client.get("/health")
    
    @task(2)
    def check_model_status(self):
        """Check model status."""
        self.client.get("/model/status")
    
    @task(1)
    def predict_audio(self):
        """Simulate audio prediction request."""
        # Create a dummy audio file for testing
        # In a real scenario, you'd use actual audio files
        audio_dir = Path("backend/data")
        
        # Try to find a real audio file, otherwise use dummy data
        audio_files = []
        if audio_dir.exists():
            for subdir in ["safe", "danger"]:
                subdir_path = audio_dir / subdir
                if subdir_path.exists():
                    audio_files.extend(list(subdir_path.glob("*.wav")))
        
        if audio_files:
            # Use a random audio file
            audio_file = random.choice(audio_files)
            with open(audio_file, 'rb') as f:
                files = {'file': (audio_file.name, f, 'audio/wav')}
                self.client.post("/predict", files=files)
        else:
            # Create a minimal dummy WAV file (44 bytes header + some data)
            # This is a minimal valid WAV file structure
            dummy_wav = (
                b'RIFF'  # ChunkID
                b'\x24\x00\x00\x00'  # ChunkSize (36 bytes)
                b'WAVE'  # Format
                b'fmt '  # Subchunk1ID
                b'\x10\x00\x00\x00'  # Subchunk1Size (16)
                b'\x01\x00'  # AudioFormat (PCM)
                b'\x01\x00'  # NumChannels (1)
                b'\x44\xAC\x00\x00'  # SampleRate (44100)
                b'\x88\x58\x01\x00'  # ByteRate
                b'\x02\x00'  # BlockAlign
                b'\x10\x00'  # BitsPerSample (16)
                b'data'  # Subchunk2ID
                b'\x00\x00\x00\x00'  # Subchunk2Size (0)
            )
            
            files = {'file': ('dummy.wav', dummy_wav, 'audio/wav')}
            self.client.post("/predict", files=files, catch_response=True)
    
    @task(1)
    def retrain_model(self):
        """Simulate retrain request (less frequent)."""
        response = self.client.post("/retrain", catch_response=True)
        # Retrain might fail if no data, that's okay
        if response.status_code in [200, 503]:
            response.success()
        else:
            response.failure(f"Unexpected status: {response.status_code}")

