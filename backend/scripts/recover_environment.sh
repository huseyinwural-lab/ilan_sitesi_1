#!/bin/bash
set -e

echo "🚀 Starting Environment Recovery..."

# 1. Start Services
echo "1. Ensuring services are running..."
service postgresql start || echo "Postgres already running"
service redis-server start || echo "Redis already running"

# 2. Recreate DB & User (Idempotent-ish)
echo "2. Setting up Database..."
sudo -u postgres psql -c "CREATE USER admin_user WITH PASSWORD 'admin_pass';" || echo "User likely exists, continuing..."
sudo -u postgres psql -c "CREATE DATABASE admin_panel OWNER admin_user;" || echo "Database likely exists, continuing..."

# 3. Run Migrations
echo "3. Running Migrations..."
cd /app/backend
alembic upgrade head

# 4. Run Seeds
echo "4. Seeding Data..."
export PYTHONPATH=/app/backend
python3 scripts/seed_countries_p19.py
python3 scripts/seed_categories_p19.py

# 5. Restart Backend
echo "5. Restarting Backend..."
supervisorctl restart backend

echo "✅ Environment Successfully Recovered!"
