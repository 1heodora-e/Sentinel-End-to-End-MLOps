#!/bin/bash
# Set TensorFlow environment variables BEFORE Python starts
export CUDA_VISIBLE_DEVICES=-1
export TF_CPP_MIN_LOG_LEVEL=2
export TF_FORCE_GPU_ALLOW_GROWTH=true
export TF_XLA_FLAGS=--tf_xla_cpu_global_jit=false
export TF_DISABLE_XLA=1

# Run uvicorn with the PORT environment variable
exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}