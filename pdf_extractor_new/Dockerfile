# PDF Extraction System - Docker Container
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements_full.txt .
RUN pip install --no-cache-dir -r requirements_full.txt

# Copy application
COPY *.py ./

# Create directories
RUN mkdir -p input output logs

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "api.py"]
