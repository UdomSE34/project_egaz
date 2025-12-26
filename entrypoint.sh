#!/bin/sh
# Exit immediately if a command fails
set -e

# Wait for DB to be ready (optional, useful if DB is in another container)
echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
exec gunicorn project_egaz.wsgi:application --bind 0.0.0.0:8000
