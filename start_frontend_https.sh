#!/bin/bash

# Start FastHTML frontend with HTTPS support
echo "🚀 Starting Voice Bot Frontend with HTTPS..."

cd fasthtml_frontend

# Set environment variables for HTTPS
export USE_HTTPS=true

# Start the frontend with SSL
python main.py

echo "✅ Frontend started with HTTPS on https://localhost:8504"
