# Use official Python runtime as base image
FROM python:3.12.3-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Render provides PORT dynamically
ENV PORT=5000

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
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY server/ .

# Create necessary directories
RUN mkdir -p /app/models_backup && \
    mkdir -p /app/static && \
    mkdir -p /app/templates

# Expose the Render port (not required but OK)
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get(f'http://localhost:{${PORT}}')" || exit 1

# Run the application with Gunicorn and Gevent
CMD ["gunicorn", "--worker-class", "gevent", "--bind", "0.0.0.0:${PORT}", "--workers", "1", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
