FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for audio processing and PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libsndfile1 \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/

# Create necessary directories
RUN mkdir -p backend/data/safe backend/data/danger backend/models

# Set TensorFlow environment variables for CPU-only execution
# These prevent CUDA initialization errors on CPU-only systems (e.g., Render)
ENV CUDA_VISIBLE_DEVICES=-1
ENV TF_CPP_MIN_LOG_LEVEL=2
ENV TF_FORCE_GPU_ALLOW_GROWTH=true
ENV TF_XLA_FLAGS=--tf_xla_cpu_global_jit=false
ENV TF_DISABLE_XLA=1

# Expose port
EXPOSE 8000

# Set working directory to backend
WORKDIR /app/backend

# Run the application (Render sets PORT automatically)
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]

