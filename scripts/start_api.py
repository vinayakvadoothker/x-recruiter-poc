#!/usr/bin/env python3
"""
Start the FastAPI server with all dependencies.

Usage:
    python scripts/start_api.py
"""

import subprocess
import sys
import time
import os
from pathlib import Path

# Change to project root
project_root = Path(__file__).parent.parent
os.chdir(project_root)

def check_docker():
    """Check if Docker is running."""
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False

def start_docker_services():
    """Start Docker services."""
    print("📦 Starting Docker services (PostgreSQL, Weaviate)...")
    subprocess.run(
        ["docker-compose", "up", "-d", "postgres", "weaviate"],
        check=True
    )
    print("⏳ Waiting for services to be ready...")
    time.sleep(3)

def run_migrations():
    """Run database migrations."""
    print("🗄️  Running database migrations...")
    try:
        subprocess.run(
            [sys.executable, "backend/database/migration_runner.py"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Migration warning: {e}")
        print("   Continuing anyway...")

def start_api():
    """Start the FastAPI server."""
    print("")
    print("✅ Starting FastAPI server on http://localhost:8000")
    print("📚 API docs available at http://localhost:8000/docs")
    print("")
    subprocess.run([
        "uvicorn",
        "backend.api.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])

if __name__ == "__main__":
    print("🚀 Starting Grok Recruiting API...")
    print("")
    
    if not check_docker():
        print("❌ Docker is not running. Please start Docker first.")
        sys.exit(1)
    
    start_docker_services()
    run_migrations()
    start_api()

