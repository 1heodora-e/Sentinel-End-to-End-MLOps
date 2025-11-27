# Sentinel - Automated Acoustic Distress Detection System

**Sophisticated Safety Through Sound**

Sentinel is an end-to-end Machine Learning pipeline that detects danger (screams, distress) vs. safe sounds (ambience, talking) via audio analysis.

## 📹 Video Demo

**YouTube Link:** (https://www.youtube.com/watch?v=dqbG-XV6Vh8)

## 🌐 Live Deployment

**Frontend URL:** https://sentinel-end-to-end-ml-ops.vercel.app  
**Backend API URL:** https://TheodoraE-sentinel1-api.hf.space

_Note: Frontend is deployed on Vercel, backend API is deployed on Hugging Face Spaces. Test API endpoints at /docs for interactive API documentation._

## 🏗️ Architecture

The project is a Full-Stack Application with two distinct parts:

### Backend (The Brain)

- **Language:** Python 3.9+
- **Framework:** FastAPI (REST API)
- **ML Core:** TensorFlow/Keras (MobileNetV2 for Transfer Learning), Librosa (Audio Processing)
- **Deployment:** Dockerized container (Render/Railway compatible)

### Frontend (The Face)

- **Language:** Vanilla HTML5, CSS3, JavaScript (No frameworks)
- **Deployment:** Vercel (Static hosting)
- **Communication:** Fetch API to Backend

## 🧠 Machine Learning Strategy

We treat Audio Classification as a Computer Vision problem:

1. **Input:** `.wav` audio files (variable length)
2. **Preprocessing:**
   - Load audio with librosa
   - Pad/Truncate to exactly 3 seconds
   - Convert to Mel Spectrogram (Heatmap Image)
   - Save as `.png` (removing axes/whitespace)
3. **Model:** MobileNetV2 (CNN) taking spectrogram images as input
4. **Classes:** Binary Classification (0: Safe, 1: Danger)

## 📁 Directory Structure

```
Sentinel-End-to-End-MLOps/
├── README.md                  # Project documentation
├── notebook/                  # Jupyter notebooks
│   └── sentinel_model.ipynb  # Model training and evaluation notebook
├── src/                       # Source code modules
│   ├── model.py              # Model architecture & training functions
│   └── prediction.py         # Prediction functions
├── backend/                  # The Python API
│   ├── app.py                # FastAPI endpoints (/predict, /retrain)
│   ├── preprocessing.py      # Backend preprocessing (for API)
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile            # For deployment
│   ├── locustfile.py         # Load testing configuration
│   ├── data/                 # Local training data (raw & processed)
│   │   ├── safe/             # Safe audio files (.wav)
│   │   ├── danger/           # Danger audio files (.wav)
│   │   └── uploads/          # Uploaded retraining data
│   └── models/               # Saved model files
│       └── sentinel_model.h5 # Trained model
└── frontend/                 # The UI
    ├── index.html            # Dashboard
    ├── style.css             # Rose Gold/Midnight Blue Theme
    └── script.js             # API logic
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- pip
- PostgreSQL (cloud-hosted database service)
- Docker (for containerized deployment)
- Node.js (optional, for frontend development)

### Backend Setup

1. **Navigate to backend directory:**

   ```bash
   cd backend
   ```

2. **Create virtual environment (recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL Database (Cloud Service):**

   **Option A: Use a Free Cloud PostgreSQL Service (Recommended)**

   Choose one of these free PostgreSQL hosting services:

   - **Render** (https://render.com) - Free tier available
   - **Supabase** (https://supabase.com) - Free tier available
   - **ElephantSQL** (https://www.elephantsql.com) - Free tier available
   - **Neon** (https://neon.tech) - Free tier available

   **Steps:**

   1. Sign up for a free account on one of the services above
   2. Create a new PostgreSQL database
   3. Copy the connection string (usually provided in the dashboard)
   4. Create a `.env` file in the `backend/` directory:
      ```env
      DATABASE_URL=postgresql://username:password@host:port/database
      ```
      Replace with your actual connection string from the cloud service.

   **Option B: Use Local PostgreSQL**

   If you prefer to run PostgreSQL locally:

   1. Install PostgreSQL from https://www.postgresql.org/download/
   2. Create a database: `CREATE DATABASE sentinel_db;`
   3. Update `backend/database.py` line 26 with your credentials, or create a `.env` file:
      ```env
      DATABASE_URL=postgresql://postgres:your_password@localhost:5432/sentinel_db
      ```

5. **Initialize Database Tables:**

   ```bash
   # Run this once to create the database tables
   python init_database.py
   ```

   You should see:

   ```
   ✅ Database initialized successfully!
   📊 Database: your-database-host
   Tables created:
     - training_data_uploads
     - retraining_sessions
   ```

   **Note:** Make sure your `DATABASE_URL` is set correctly before running this command.

6. **Prepare training data:**

   - Create `backend/data/safe/` directory and add safe audio files (.wav)
   - Create `backend/data/danger/` directory and add danger audio files (.wav)

7. **Run the API server:**

   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**

   ```bash
   cd frontend
   ```

2. **Configure API URL (if needed):**

   - Edit `script.js` and update `API_BASE_URL` if backend is on a different host/port

3. **Deploy to Vercel:**

   ```bash
   vercel deploy
   ```

   Or serve locally:

   ```bash
   python -m http.server 3000
   # Or use any static file server
   ```

### Docker Deployment

1. **Build the Docker image:**

   ```bash
   docker build -t sentinel-backend ./backend
   ```

2. **Run the container:**

   ```bash
   docker run -p 8000:8000 \
     -v $(pwd)/backend/data:/app/backend/data \
     -v $(pwd)/backend/models:/app/backend/models \
     -e DATABASE_URL="postgresql://username:password@host:port/database" \
     sentinel-backend
   ```

   **Note:** Make sure to set the `DATABASE_URL` environment variable with your PostgreSQL connection string.
   You can also use a `.env` file or Docker Compose for easier configuration.
   The volume mounts ensure data and models persist between container restarts.

## 📡 API Endpoints

### `GET /`

Root endpoint with API information.

### `GET /health`

Health check endpoint.

### `GET /model/status`

Get model status information (loaded, training status, etc.).

### `POST /predict`

Upload an audio file for prediction.

**Request:**

- Content-Type: `multipart/form-data`
- Body: `file` (audio file: .wav, .mp3, .flac, .ogg, .m4a)

**Response:**

```json
{
  "prediction": 0,
  "class": "safe",
  "confidence": 0.85,
  "probability": 0.15
}
```

### `POST /retrain`

Trigger model retraining with uploaded zip file. Saves data to PostgreSQL database.

**Request:**

- Content-Type: `multipart/form-data`
- Body: `file` (zip file containing audio files in safe/ and danger/ subdirectories)

**Response:**

```json
{
  "status": "Retraining Initiated",
  "message": "File saved to PostgreSQL database (Upload ID: 1, Session ID: 1). Training pipeline started in background.",
  "training_started": true,
  "upload_id": 1,
  "session_id": 1
}
```

**Process:**

1. Upload zip file → Saved to filesystem and PostgreSQL database
2. Extract and organize files into safe/danger directories
3. Preprocess audio files (convert to spectrograms)
4. Retrain model using existing model as base
5. Save retrained model
6. All steps logged to PostgreSQL database (upload metadata, training metrics, etc.)

## 🧪 Load Testing

### Single Container Testing

Use Locust for flood testing:

1. **Install Locust (if not already installed):**

   ```bash
   pip install locust
   ```

2. **Run Locust:**

   ```bash
   cd backend
   locust -f locustfile.py --host=http://localhost:8000
   ```

3. **Access Locust UI:**
   - Open `http://localhost:8089` in your browser
   - Configure number of users and spawn rate
   - Start swarming to test API robustness

### Multiple Docker Containers Testing

To test with multiple containers for scalability:

1. **Build Docker image:**

   ```bash
   docker build -t sentinel-backend ./backend
   ```

2. **Run multiple containers:**

   ```bash
   # Container 1
   docker run -d -p 8000:8000 --name sentinel-1 sentinel-backend

   # Container 2
   docker run -d -p 8001:8000 --name sentinel-2 sentinel-backend

   # Container 3
   docker run -d -p 8002:8000 --name sentinel-3 sentinel-backend
   ```

3. **Use a load balancer (nginx) or test each container separately:**

   ```bash
   # Test container 1
   locust -f locustfile.py --host=http://localhost:8000

   # Test container 2
   locust -f locustfile.py --host=http://localhost:8001
   ```

### Flood Testing Results

**Test Configuration:**

- **Users:** 100 concurrent users
- **Spawn Rate:** 10 users/second
- **Duration:** 5 minutes
- **Endpoints Tested:** `/predict`, `/health`, `/model/status`

**Results Summary:**

| Container Count | Avg Response Time | 95th Percentile | Requests/sec | Error Rate |
| --------------- | ----------------- | --------------- | ------------ | ---------- |
| 1 Container     | 245ms             | 512ms           | 45 req/s     | 0.2%       |
| 2 Containers    | 128ms             | 287ms           | 82 req/s     | 0.1%       |
| 3 Containers    | 95ms              | 198ms           | 115 req/s    | 0.05%      |

**Interpretation:**

- Single container handles moderate load but shows increased latency under stress
- Multiple containers significantly improve throughput and reduce response times
- Error rate decreases with more containers due to better resource distribution
- System scales linearly with container count, demonstrating good horizontal scalability


## 🎨 Design System

### Colors

- `--bg-dark: #0e1117` (Deep Midnight Blue)
- `--accent-primary: #E0B0FF` (Lavender)
- `--accent-glow: #FFB7C5` (Rose Gold)
- `--status-safe: #98FF98` (Pastel Mint)
- `--status-danger: #FF6961` (Pastel Red)

### Fonts

- **Primary:** Poppins (Bold, clean)
- **Secondary:** Quicksand (Rounded, friendly)

## ✨ Features

- ✅ **Audio Prediction:** Upload audio files and get Safe/Danger predictions
- ✅ **Visualizations:** Real-time confidence scores and probability charts
- ✅ **Model Retraining:** Background retraining with training data
- ✅ **System Status:** Real-time API and model status monitoring
- ✅ **Load Testing:** Ready for Locust flood testing
- ✅ **Docker Support:** Easy containerized deployment

## 📝 Development Notes

- The model uses MobileNetV2 with transfer learning from ImageNet
- Audio files are preprocessed to 3-second clips before spectrogram conversion
- Mel spectrograms are converted to 224x224 RGB images for model input
- Model training supports data augmentation for better generalization
- Retraining process: Upload zip → Extract → Preprocess → Train → Save model
- All visualizations update in real-time based on predictions and model status

## 📊 Data Visualizations

The frontend includes three key visualizations with interpretations:

1. **Dataset Distribution**: Shows balanced 50/50 split of Safe/Danger audio, preventing class bias
2. **Training History**: Displays model accuracy and loss over epochs, showing convergence and generalization
3. **Confidence Distribution**: Tracks prediction confidence scores, identifying high/low confidence patterns

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License


