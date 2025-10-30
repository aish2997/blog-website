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

# Read .env file if it exists (for local development)
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(str(env_file))
    print(f"✅ Loaded environment variables from {env_file}")

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
    'django.contrib.sites',  # Required by django-allauth

    # django-allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # Third-party apps
    'taggit',
    'markdownx',
    'hitcount',
    'whitenoise.runserver_nostatic',
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
    'allauth.account.middleware.AccountMiddleware',  # Required by django-allauth
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
# PostgreSQL for production (using Neon serverless PostgreSQL)
# Falls back to SQLite for local testing if DATABASE_URL is not set

import dj_database_url

# Check for PostgreSQL connection string (Neon or other PostgreSQL provider)
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Production: Use PostgreSQL (Neon)
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,  # Connection pooling
            conn_health_checks=True,  # Check connection health
            ssl_require=True,  # Require SSL for security
        )
    }

    # PostgreSQL-specific settings for better performance
    # Note: Neon pooler doesn't support statement_timeout in startup parameters
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 10,
    }
else:
    # Fallback: Use SQLite for local development/testing
    # Note: /tmp is the only writable directory in Cloud Run
    DATABASE_PATH = os.environ.get('DATABASE_PATH', '/tmp/db.sqlite3')
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': DATABASE_PATH,
            'OPTIONS': {
                'timeout': 20,
            }
        }
    }

    print("WARNING: Using SQLite database. Set DATABASE_URL environment variable for PostgreSQL.")

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

# Configure STORAGES for Django 4.2+
STORAGES = {}

# Configure static files storage
if GCS_BUCKET_STATIC:
    # Use GCS for static files
    STORAGES["staticfiles"] = {
        "BACKEND": "portfolio.storage_backends.StaticStorage",
    }
    STATIC_URL = f'https://storage.googleapis.com/{GCS_BUCKET_STATIC}/'
    print(f"✅ Using GCS for static files: {GCS_BUCKET_STATIC}")
else:
    # Fallback to WhiteNoise with optimized settings
    STORAGES["staticfiles"] = {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
    STATIC_URL = '/static/'

    # WhiteNoise configuration for proper admin static file serving
    WHITENOISE_USE_FINDERS = True  # Find static files from all apps
    WHITENOISE_AUTOREFRESH = False  # Don't refresh in production
    WHITENOISE_COMPRESS_OFFLINE = True  # Pre-compress files
    WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz']
    # Ensure proper MIME types for CSS and JS
    WHITENOISE_MIMETYPES = {
        '.css': 'text/css',
        '.js': 'application/javascript',
    }
    # Cache static files for 1 year (they have cache-busting hashes)
    WHITENOISE_MAX_AGE = 31536000

    print("✅ Using WhiteNoise for static files with optimized settings")

# Configure media files storage (default storage)
if GCS_BUCKET_MEDIA:
    # Use GCS for media files
    STORAGES["default"] = {
        "BACKEND": "portfolio.storage_backends.MediaStorage",
    }
    MEDIA_URL = f'https://storage.googleapis.com/{GCS_BUCKET_MEDIA}/'
    print(f"✅ Using GCS for media files: {GCS_BUCKET_MEDIA}")
else:
    # Use local filesystem for media
    STORAGES["default"] = {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    }
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
        'simple': {
            'format': '{levelname} {asctime} {message}',
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
        # Capture Django request/response errors (including 500 errors)
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        # Capture database query errors
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        # Capture errors in comments app (orphaned comments, admin issues)
        'apps.comments': {
            'handlers': ['console'],
            'level': 'WARNING',  # Capture warnings about orphaned comments
            'propagate': False,
        },
        # Capture errors in blog and projects apps
        'apps.blog': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps.projects': {
            'handlers': ['console'],
            'level': 'WARNING',
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

# django-allauth Configuration
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# allauth settings
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

# Social account settings
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_STORE_TOKENS = True

# Google OAuth provider configuration
# Note: Client ID and Secret are configured via Django Admin (Social Applications)
# NOT via settings, to avoid conflicts
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'FETCH_USERINFO': True,
    }
}