#!/bin/bash

echo "Starting build process..."

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Run database migrations
echo "Running migrations..."
python manage.py migrate --noinput

echo "Build completed successfully!"
