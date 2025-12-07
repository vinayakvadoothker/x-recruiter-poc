FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (both Vin's and Ishaan's)
COPY requirements-vin.txt .
COPY requirements.txt .

# Install Python dependencies (both files)
RUN pip install --no-cache-dir -r requirements-vin.txt && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY tests/ ./tests/

# Set Python path
ENV PYTHONPATH=/app

# Default command (can be overridden)
CMD ["python", "-m", "pytest", "tests/", "-v"]

