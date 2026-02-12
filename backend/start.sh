#!/bin/bash
set -e

# 1. Run Migrations
echo "Running database migrations..."
alembic upgrade head

# 2. Start Application
echo "Starting Uvicorn server..."
# Use $PORT provided by Render, default to 10000 if not set
exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-10000}
