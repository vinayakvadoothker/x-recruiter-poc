FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-vin.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-vin.txt

# Copy application code
COPY backend/ ./backend/
COPY tests/ ./tests/

# Set Python path
ENV PYTHONPATH=/app

# Default command (can be overridden)
CMD ["python", "-m", "pytest", "tests/", "-v"]

