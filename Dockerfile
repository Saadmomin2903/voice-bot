# Multi-stage Dockerfile for Voice Bot
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements files
COPY backend/requirements.txt /app/backend/requirements.txt
COPY fasthtml_frontend/requirements.txt /app/fasthtml_frontend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt
RUN pip install --no-cache-dir -r fasthtml_frontend/requirements.txt

# Copy application code
COPY . /app/

# Create SSL certificates directory
RUN mkdir -p /app/ssl_certs

# Copy SSL certificates (only .gitkeep file exists in repo)
COPY ssl_certs/ /app/ssl_certs/

# Make startup script executable
RUN chmod +x /app/start_render_simple.py

# Expose port
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10000/health || exit 1

# Start the application
CMD ["python", "start_render_simple.py"]
