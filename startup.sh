#!/bin/bash
# Startup script for Azure App Service (Linux)
# This script prepares the Django app for production

set -e

echo "=== Starting Dashboard Application ==="
echo "Time: $(date)"
echo ""

# Upgrade pip
echo "[1/5] Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "[2/5] Installing dependencies..."
pip install -r requirements.txt

# Collect static files
echo "[3/5] Collecting static files..."
python manage.py collectstatic --noinput || echo "WARNING: Static files collection failed (non-critical)"

# Run migrations
echo "[4/5] Running database migrations..."
python manage.py migrate

# Start the application
echo "[5/5] Starting Django application..."
echo "Listening on 0.0.0.0:${PORT:-8000}"
echo ""
python run_waitress.py

# If we reach here, the app crashed
exit 1

