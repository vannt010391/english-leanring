"""
Production settings for VocabMaster project.
"""
from .settings import *

# Production settings
DEBUG = False
ALLOWED_HOSTS = ['english.iamstudying.tech', 'www.english.iamstudying.tech', '178.128.58.51', 'localhost', '127.0.0.1']

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Static files
STATIC_ROOT = '/var/www/vocabmaster/vocab_project/staticfiles'
STATIC_URL = '/static/'

# Media files
MEDIA_ROOT = '/var/www/vocabmaster/vocab_project/media'
MEDIA_URL = '/media/'

# Whitenoise for static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# CSRF settings
CSRF_TRUSTED_ORIGINS = [
    'https://english.iamstudying.tech',
    'https://www.english.iamstudying.tech',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]
CSRF_USE_SESSIONS = True

# Login URL for @login_required redirects
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'

# CORS settings for production
CORS_ALLOW_CREDENTIALS = True
