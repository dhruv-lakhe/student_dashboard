import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_dashboard.settings')

from waitress import serve

from student_dashboard.wsgi import application

print("Starting waitress server on http://localhost:8000/")
print("Press Ctrl+C to stop")

try:
    serve(application, host='localhost', port=8000, threads=4)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

