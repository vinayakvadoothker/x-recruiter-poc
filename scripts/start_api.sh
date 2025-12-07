#!/bin/bash
# Start the FastAPI server

cd "$(dirname "$0")/.." || exit

echo "🚀 Starting Grok Recruiting API..."
echo ""

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start Docker services if not running
echo "📦 Starting Docker services (PostgreSQL, Weaviate)..."
docker-compose up -d postgres weaviate

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 3

# Run migrations
echo "🗄️  Running database migrations..."
python backend/database/migration_runner.py

# Start the API
echo ""
echo "✅ Starting FastAPI server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo ""
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

