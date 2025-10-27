"""
Production settings for portfolio project.
"""
import os
from pathlib import Path
import environ
from google.cloud import secretmanager

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env()

# GCP Project ID
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')

# Initialize Secret Manager client
if GCP_PROJECT_ID:
    client = secretmanager.SecretManagerServiceClient()

    def get_secret(secret_id):
        """Retrieve secret from GCP Secret Manager"""
        try:
            name = f"projects/{GCP_PROJECT_ID}/secrets/{secret_id}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            # Fallback to environment variable
            return os.environ.get(secret_id.upper().replace('-', '_'), '')
else:
    def get_secret(secret_id):
        return os.environ.get(secret_id.upper().replace('-', '_'), '')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY') or get_secret('django-secret-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Allow Cloud Run domains and any custom domains
ALLOWED_HOSTS_ENV = os.environ.get('ALLOWED_HOSTS', '')
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS = ALLOWED_HOSTS_ENV.split(',')
else:
    # Default to allowing Cloud Run domains
    ALLOWED_HOSTS = [
        '.run.app',  # All Cloud Run domains
        '.europe-west1.run.app',  # Specific region
        '.us-central1.run.app',   # Another common region
        'localhost',
        '127.0.0.1',
    ]

# Add any custom domain if provided
if os.environ.get('CUSTOM_DOMAIN'):
    ALLOWED_HOSTS.append(os.environ.get('CUSTOM_DOMAIN'))

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
    'markdownify',
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
DATABASE_PATH = os.environ.get('DATABASE_PATH', '/app/data/db.sqlite3')

# Ensure the data directory exists
import os
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATABASE_PATH,
        'OPTIONS': {
            # SQLite optimizations for better performance
            'init_command': "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA cache_size=10000; PRAGMA temp_store=MEMORY;",
            'timeout': 20,
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

# Static files (CSS, JavaScript, Images) - Using Google Cloud Storage
if os.environ.get('GCS_BUCKET_STATIC'):
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

    GS_BUCKET_NAME = os.environ.get('GCS_BUCKET_STATIC')
    GS_DEFAULT_ACL = 'publicRead'

    STATIC_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'
else:
    # Fallback to WhiteNoise for local serving
    STATIC_URL = '/static/'
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if os.path.exists(BASE_DIR / 'static') else []

# Media files - Using Google Cloud Storage
if os.environ.get('GCS_BUCKET_MEDIA'):
    GS_MEDIA_BUCKET_NAME = os.environ.get('GCS_BUCKET_MEDIA')
    MEDIA_URL = f'https://storage.googleapis.com/{GS_MEDIA_BUCKET_NAME}/'

    # Custom storage for media files
    DEFAULT_FILE_STORAGE = 'portfolio.storage_backends.MediaStorage'
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

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

# Security settings for production
# Cloud Run handles SSL termination at the load balancer level
# The connection from load balancer to container is HTTP, so we must not redirect
SECURE_SSL_REDIRECT = False

# Tell Django to trust the X-Forwarded-Proto header from Cloud Run's proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Keep cookies secure since the user connection is HTTPS
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Other security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS headers - Cloud Run supports these
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# CSRF settings for Cloud Run
CSRF_TRUSTED_ORIGINS = [
    'https://*.run.app',  # All Cloud Run domains
    'https://*.europe-west1.run.app',
    'https://*.us-central1.run.app',
    'https://*.ew.run.app',  # Short region codes
    'https://*.uc.run.app',
]

# Add specific Cloud Run service URL if provided
if os.environ.get('CLOUD_RUN_SERVICE_URL'):
    CSRF_TRUSTED_ORIGINS.append(os.environ.get('CLOUD_RUN_SERVICE_URL'))

# Add custom domain if provided
if os.environ.get('CUSTOM_DOMAIN'):
    CSRF_TRUSTED_ORIGINS.append(f"https://{os.environ.get('CUSTOM_DOMAIN')}")

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