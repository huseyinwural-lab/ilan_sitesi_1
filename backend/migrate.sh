#!/bin/bash
set -e

echo "Starting deployment migration..."
echo "Applying alembic upgrade head..."

if alembic upgrade head; then
    echo "Migration completed successfully."
else
    echo "Migration FAILED. Aborting deployment."
    exit 1
fi
