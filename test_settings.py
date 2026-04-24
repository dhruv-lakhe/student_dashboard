import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_dashboard.settings')

import django

django.setup()

from django.conf import settings

print('STATIC_ROOT:', settings.STATIC_ROOT)
print('STATIC_URL:', settings.STATIC_URL)
print('STATICFILES_STORAGE:', settings.STATICFILES_STORAGE)
print('MIDDLEWARE:')
for m in settings.MIDDLEWARE:
    print('  ', m)
    print('  ', m)
