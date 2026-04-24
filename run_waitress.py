import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_dashboard.settings')

from waitress import serve

from student_dashboard.wsgi import application

# Get port from environment variable or default to 8000
port = int(os.environ.get('PORT', 8000))
host = '0.0.0.0'  # Listen on all interfaces for Azure App Service

print(f"Starting waitress server on http://{host}:{port}/")
print("Press Ctrl+C to stop")

try:
    serve(application, host=host, port=port, threads=4)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

