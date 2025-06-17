#!/bin/bash

# Startup script for Cloud Run
echo "Starting application..."

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn server..."
exec gunicorn --config gunicorn.conf.py group_ordering_app.wsgi:application
