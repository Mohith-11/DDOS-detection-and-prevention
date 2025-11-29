# Use official Python runtime as base image
FROM python:3.12.3-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY server/requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project files
COPY server/ .

# Create necessary directories
RUN mkdir -p /app/models_backup && \
    mkdir -p /app/static && \
    mkdir -p /app/templates

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000')" || exit 1

# Run the application with Gunicorn
CMD ["gunicorn", "--worker-class", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", \
     "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "60", "wsgi:app"]
