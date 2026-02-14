"""
Development settings — DEBUG on, permissive security, SQLite OK.
Use: DJANGO_ENV=development (default) or DJANGO_SETTINGS_MODULE=config.settings.development.
"""
from decouple import config
from .base import *  # noqa: F401, F403

SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-only-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Development: allow browsable API if needed
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
]
