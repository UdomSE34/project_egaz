#!/bin/sh

echo "Starting Django application..."

# Optional: wait for DB (important for Supabase / cloud DB)
echo "Waiting for database..."
sleep 5

# Run migrations safely
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn project_egaz.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120
