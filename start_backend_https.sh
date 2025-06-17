#!/bin/bash

# Start FastAPI backend with HTTPS support
echo "🚀 Starting Voice Bot Backend with HTTPS..."

cd backend

# Set environment variables for HTTPS
export USE_SSL=true
export HOST=0.0.0.0
export PORT=8000
export DEBUG=true

# Start the backend with SSL
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 --ssl-keyfile ../ssl_certs/key.pem --ssl-certfile ../ssl_certs/cert.pem

echo "✅ Backend started with HTTPS on https://localhost:8000"
echo "📚 API Documentation: https://localhost:8000/docs"
