---
title: Sentinel API
emoji: 🎵
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# Sentinel - Audio Distress Detection API

FastAPI endpoint for detecting danger vs safe sounds in audio files using deep learning.

## 🎯 Overview

Sentinel is an end-to-end Machine Learning pipeline that analyzes audio files to classify them as either:
- **Safe**: Normal ambient sounds, talking, music
- **Danger**: Screams, distress calls, emergency sounds

## 📡 API Endpoints

- `POST /predict` - Upload audio file (WAV/MP3) for real-time prediction
- `POST /retrain` - Upload dataset (ZIP) to retrain the model
- `GET /model/status` - Check model status, accuracy, and training state
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)

## 🚀 Quick Start

1. Visit `/docs` for interactive API documentation
2. Upload an audio file via `/predict` endpoint
3. Receive prediction with confidence score

## 🔧 Technical Details

- **Framework**: FastAPI
- **ML Model**: MobileNetV2 (Transfer Learning)
- **Audio Processing**: Librosa (Mel Spectrograms)
- **Deployment**: Docker on Hugging Face Spaces

## 📝 Example Usage

### Predict Audio
```bash
curl -X POST "https://your-space.hf.space/predict" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.wav"
```

### Check Model Status
```bash
curl -X GET "https://your-space.hf.space/model/status"
```

## 📊 Model Information

- **Architecture**: MobileNetV2 (pretrained on ImageNet)
- **Input**: 224x224 RGB Mel Spectrogram images
- **Output**: Binary classification (Safe/Danger)
- **Accuracy**: Check via `/model/status` endpoint

## 🔒 Environment Variables

Set these in Hugging Face Space settings:
- `DATABASE_URL` - PostgreSQL connection string (optional, for retraining history)

## 📚 Documentation

Full API documentation available at `/docs` endpoint.

