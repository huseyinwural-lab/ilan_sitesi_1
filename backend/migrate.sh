#!/bin/bash
set -e
echo "Running pre-deploy database migrations..."
alembic upgrade head
