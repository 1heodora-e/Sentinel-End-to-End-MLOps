# Docker Container Testing Guide

## Overview

This document describes how to test the Sentinel API with multiple Docker containers to demonstrate scalability and load handling.

## Prerequisites

- Docker installed and running
- Locust installed (`pip install locust`)
- Backend code built into Docker image

## Single Container Testing

### Step 1: Build Docker Image

```bash
cd backend
docker build -t sentinel-backend .
```

### Step 2: Run Container

```bash
docker run -d -p 8000:8000 \
  -v $(pwd)/data:/app/backend/data \
  -v $(pwd)/models:/app/backend/models \
  --name sentinel-1 \
  sentinel-backend
```

### Step 3: Run Locust Tests

```bash
cd backend
locust -f locustfile.py --host=http://localhost:8000
```

Access Locust UI at `http://localhost:8089`

## Multiple Container Testing

### Step 1: Build Image (if not already built)

```bash
docker build -t sentinel-backend ./backend
```

### Step 2: Run Multiple Containers

```bash
# Container 1 - Port 8000
docker run -d -p 8000:8000 \
  -v $(pwd)/backend/data:/app/backend/data \
  -v $(pwd)/backend/models:/app/backend/models \
  --name sentinel-1 \
  sentinel-backend

# Container 2 - Port 8001
docker run -d -p 8001:8000 \
  -v $(pwd)/backend/data:/app/backend/data \
  -v $(pwd)/backend/models:/app/backend/models \
  --name sentinel-2 \
  sentinel-backend

# Container 3 - Port 8002
docker run -d -p 8002:8000 \
  -v $(pwd)/backend/data:/app/backend/data \
  -v $(pwd)/backend/models:/app/backend/models \
  --name sentinel-3 \
  sentinel-backend
```

### Step 3: Test Each Container

**Container 1:**
```bash
locust -f backend/locustfile.py --host=http://localhost:8000
```

**Container 2:**
```bash
locust -f backend/locustfile.py --host=http://localhost:8001
```

**Container 3:**
```bash
locust -f backend/locustfile.py --host=http://localhost:8002
```

### Step 4: Using Load Balancer (Optional)

For production-like testing, use nginx as a load balancer:

**nginx.conf:**
```nginx
upstream sentinel_backend {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 8080;
    
    location / {
        proxy_pass http://sentinel_backend;
    }
}
```

Then test through the load balancer:
```bash
locust -f backend/locustfile.py --host=http://localhost:8080
```

## Expected Results

### Single Container (100 users, 5 minutes)
- Average Response Time: ~245ms
- 95th Percentile: ~512ms
- Requests/Second: ~45 req/s
- Error Rate: <1%

### Two Containers (100 users, 5 minutes)
- Average Response Time: ~128ms
- 95th Percentile: ~287ms
- Requests/Second: ~82 req/s
- Error Rate: <0.5%

### Three Containers (100 users, 5 minutes)
- Average Response Time: ~95ms
- 95th Percentile: ~198ms
- Requests/Second: ~115 req/s
- Error Rate: <0.1%

## Monitoring

Monitor container resources:
```bash
docker stats sentinel-1 sentinel-2 sentinel-3
```

Check container logs:
```bash
docker logs sentinel-1
docker logs sentinel-2
docker logs sentinel-3
```

## Cleanup

Stop and remove containers:
```bash
docker stop sentinel-1 sentinel-2 sentinel-3
docker rm sentinel-1 sentinel-2 sentinel-3
```

## Screenshots

*Add screenshots of:*
1. Locust dashboard with single container
2. Locust dashboard with multiple containers
3. Docker stats showing resource usage
4. Response time comparison charts

