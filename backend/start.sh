#!/bin/bash
set -e

# Start Application
echo "Starting Uvicorn server..."
exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-10000}
