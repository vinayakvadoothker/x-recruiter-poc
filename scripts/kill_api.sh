#!/bin/bash
# Kill any process running on port 8000

echo "🔪 Killing process on port 8000..."

if lsof -ti:8000 > /dev/null 2>&1; then
    lsof -ti:8000 | xargs kill -9
    echo "✅ Killed process on port 8000"
else
    echo "ℹ️  No process found on port 8000"
fi

