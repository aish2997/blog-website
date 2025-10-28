"""
Production settings for portfolio project.
"""
import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env()

# GCP Project ID
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')

# SECRET KEY - Critical for security, no fallbacks allowed in production
# Cloud Run will inject this from Secret Manager automatically
SECRET_KEY = os.environ.get('SECRET_KEY')

# Import sys to check if we're running collectstatic
import sys
IS_COLLECTING_STATIC = 'collectstatic' in sys.argv

# Fail fast if SECRET_KEY is not set - EXCEPT during collectstatic in build
if not SECRET_KEY:
    from django.core.exceptions import ImproperlyConfigured

    # Allow missing SECRET_KEY only during collectstatic (build phase)
    if IS_COLLECTING_STATIC:
        print("⚠️  WARNING: Using temporary SECRET_KEY for collectstatic only (build phase)")
        SECRET_KEY = 'temporary-key-for-collectstatic-only'
    else:
        error_msg = """
        ❌ CRITICAL ERROR: SECRET_KEY environment variable is not set!

        This is a security requirement and the application cannot start without it.
        The SECRET_KEY should be provided by Cloud Run from Secret Manager.

        If running locally, set: export SECRET_KEY='your-dev-secret-key'
        If on Cloud Run, ensure the secret is configured in Terraform and has a value in Secret Manager.
        """
        print(error_msg)
        raise ImproperlyConfigured("SECRET_KEY environment variable is required and must be set!")

# Additional validation - but skip during collectstatic
if not IS_COLLECTING_STATIC:
    # Check for build-time key that shouldn't be used at runtime
    if SECRET_KEY == 'build-time-key-only-for-collectstatic-not-for-production':
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("Build-time SECRET_KEY detected at runtime! Real SECRET_KEY must be provided by Cloud Run.")

    # Check for other placeholder values
    if SECRET_KEY in ['INSECURE', 'CHANGEME', 'REPLACE', 'TODO', 'temporary-key-for-collectstatic-only'] or len(SECRET_KEY) < 50:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("SECRET_KEY appears to be a placeholder or too short. Please use a proper secret key!")

    print("✅ SECRET_KEY loaded successfully from environment")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# Application definition
INSTALLED_APPS = [
    # Django default apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.humanize',

    # Third-party apps
    'taggit',
    'markdownx',
    'hitcount',
    # 'whitenoise.runserver_nostatic',  # REMOVED - This breaks static files in production!
    'django_extensions',
    'storages',  # For Google Cloud Storage

    # Our apps
    'apps.core',
    'apps.blog',
    'apps.projects',
    'apps.analytics',
    'apps.comments',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'portfolio.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'apps.core.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'portfolio.wsgi.application'

# Database
# Using SQLite for production (cost-effective for low-traffic portfolio site)
# Note: /tmp is the only writable directory in Cloud Run
DATABASE_PATH = os.environ.get('DATABASE_PATH', '/tmp/db.sqlite3')

# Ensure the data directory exists
import os
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATABASE_PATH,
        'OPTIONS': {
            # SQLite timeout setting
            'timeout': 20,
            # Note: PRAGMA optimizations are applied via signal in apps.core.apps
        }
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Storage Configuration
GCS_BUCKET_MEDIA = os.environ.get('GCS_BUCKET_MEDIA')
GCS_BUCKET_STATIC = os.environ.get('GCS_BUCKET_STATIC')

# Configure static files storage
if GCS_BUCKET_STATIC:
    # Use GCS for static files with Django 4.2+ STORAGES
    STORAGES = {
        "staticfiles": {
            "BACKEND": "portfolio.storage_backends.StaticStorage",
        }
    }
    STATIC_URL = f'https://storage.googleapis.com/{GCS_BUCKET_STATIC}/'
    print(f"✅ Using GCS for static files: {GCS_BUCKET_STATIC}")
else:
    # Use WhiteNoise with traditional configuration
    # DO NOT use STORAGES when using STATICFILES_STORAGE
    STATIC_URL = '/static/'
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

    # These settings will now actually be used by WhiteNoise:
    WHITENOISE_USE_FINDERS = True  # Critical: allows WhiteNoise to find admin files
    WHITENOISE_AUTOREFRESH = False  # Don't refresh in production
    WHITENOISE_MAX_AGE = 31536000  # Cache for 1 year

    print("✅ Using WhiteNoise for static files (traditional configuration)")

# Configure media files storage
if GCS_BUCKET_STATIC:
    # If using STORAGES for static files, also use it for media
    if GCS_BUCKET_MEDIA:
        STORAGES["default"] = {
            "BACKEND": "portfolio.storage_backends.MediaStorage",
        }
        MEDIA_URL = f'https://storage.googleapis.com/{GCS_BUCKET_MEDIA}/'
        print(f"✅ Using GCS for media files: {GCS_BUCKET_MEDIA}")
    else:
        STORAGES["default"] = {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        }
        MEDIA_URL = '/media/'
        print("⚠️ Using local filesystem for media files")
else:
    # If using traditional configuration for static files, use it for media too
    if GCS_BUCKET_MEDIA:
        DEFAULT_FILE_STORAGE = 'portfolio.storage_backends.MediaStorage'
        MEDIA_URL = f'https://storage.googleapis.com/{GCS_BUCKET_MEDIA}/'
        print(f"✅ Using GCS for media files: {GCS_BUCKET_MEDIA}")
    else:
        # Use Django's default (no need to specify)
        MEDIA_URL = '/media/'
        print("⚠️ Using local filesystem for media files")

# Always set these regardless of storage backend
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Ensure static directory is always included (create if it doesn't exist)
static_dir = BASE_DIR / 'static'
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)
STATICFILES_DIRS = [static_dir]

# Configure static file finders to ensure admin files are found
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',  # Find files in STATICFILES_DIRS
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',  # Find files in app static/ directories
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Markdown settings
MARKDOWNX_MARKDOWN_EXTENSIONS = [
    'markdown.extensions.fenced_code',
    'markdown.extensions.codehilite',
    'markdown.extensions.tables',
    'markdown.extensions.nl2br',
    'markdown.extensions.toc',
]

MARKDOWNX_EDITOR_RESIZABLE = True
MARKDOWNX_IMAGE_MAX_SIZE = {'size': (800, 0), 'quality': 90}
MARKDOWNX_MEDIA_PATH = 'markdownx/'

# Taggit settings
TAGGIT_CASE_INSENSITIVE = True

# Cloud Run SSL termination handling
# Cloud Run terminates SSL at the edge and forwards HTTP to the container
# We need to trust the X-Forwarded-Proto header to detect HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Security settings for production
# Only redirect to HTTPS if we're in production and NOT on Cloud Run
# Cloud Run handles SSL termination at the edge
SECURE_SSL_REDIRECT = not DEBUG and not os.environ.get('K_SERVICE')
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# CSRF settings for Cloud Run
CSRF_TRUSTED_ORIGINS = []

# Add Cloud Run service URL
cloud_run_url = os.environ.get('CLOUD_RUN_SERVICE_URL')
if cloud_run_url:
    CSRF_TRUSTED_ORIGINS.append(cloud_run_url)

# Add custom domain if configured
if os.environ.get('CUSTOM_DOMAIN'):
    CSRF_TRUSTED_ORIGINS.append(f"https://{os.environ.get('CUSTOM_DOMAIN')}")

# Fallback to allow the autogenerated Cloud Run URL pattern
if not CSRF_TRUSTED_ORIGINS and ALLOWED_HOSTS == ['*']:
    # Allow any Cloud Run domain during initial deployment
    CSRF_TRUSTED_ORIGINS = [
        'https://*.run.app',
        'https://*.a.run.app'
    ]

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Site Configuration from environment
SITE_CONFIG = {
    'name': os.environ.get('SITE_NAME', 'Portfolio'),
    'description': os.environ.get('SITE_DESCRIPTION', 'Full Stack Developer'),
    'github_url': os.environ.get('GITHUB_URL', ''),
    'linkedin_url': os.environ.get('LINKEDIN_URL', ''),
    'twitter_url': os.environ.get('TWITTER_URL', ''),
    'email': os.environ.get('EMAIL_CONTACT', ''),
    'profile_image': os.environ.get('PROFILE_IMAGE_PATH', 'profile.jpg'),
}

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@example.com')