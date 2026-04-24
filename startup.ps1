# Startup script for Azure App Service
# This script prepares the Django app for production

$python = python.exe
$pip = python.exe -m pip

# Upgrade pip
Write-Host "Upgrading pip..."
& $pip install --upgrade pip

# Install requirements
Write-Host "Installing dependencies..."
& $pip install -r requirements.txt

# Collect static files
Write-Host "Collecting static files..."
& $python manage.py collectstatic --noinput

# Run migrations
Write-Host "Running database migrations..."
& $python manage.py migrate

# Start the application
Write-Host "Starting Django application..."
& $python run_waitress.py
