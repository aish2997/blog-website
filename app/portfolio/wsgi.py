"""
WSGI config for portfolio project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Determine which settings to use
if os.environ.get('K_SERVICE'):  # Running on Cloud Run
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio.settings_production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio.settings')

application = get_wsgi_application()
