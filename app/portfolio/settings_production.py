"""
Production settings for portfolio project.
"""
import os
from pathlib import Path
import environ
from google.cloud import secretmanager
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env()

# GCP Project ID
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')

# SECRET KEY - with multiple fallback mechanisms
SECRET_KEY = None

# Try environment variable first
SECRET_KEY = os.environ.get('SECRET_KEY')

# If not found and we have GCP_PROJECT_ID, try Secret Manager
if not SECRET_KEY and GCP_PROJECT_ID:
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{GCP_PROJECT_ID}/secrets/django-secret-key/versions/latest"
        response = client.access_secret_version(request={"name": name})
        SECRET_KEY = response.payload.data.decode("UTF-8")
        print(f"✅ Secret key loaded from Secret Manager")
    except Exception as e:
        print(f"⚠️ Could not load secret from Secret Manager: {e}")

# No fallback - fail fast if SECRET_KEY is not configured
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "SECRET_KEY must be set in production! "
        "Set the SECRET_KEY environment variable or configure Google Cloud Secret Manager."
    )

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# ALLOWED_HOSTS must be explicitly set - no wildcards in production
ALLOWED_HOSTS_STR = os.environ.get('ALLOWED_HOSTS', '')
if not ALLOWED_HOSTS_STR:
    # In Cloud Run, we can get the service URL
    cloud_run_service = os.environ.get('K_SERVICE')
    cloud_run_region = os.environ.get('K_CONFIGURATION')
    if cloud_run_service:
        # Auto-configure for Cloud Run if no explicit hosts set
        ALLOWED_HOSTS = [
            f'{cloud_run_service}-*.run.app',
            f'{cloud_run_service}-*.a.run.app',
            'localhost',  # For health checks
            '127.0.0.1',
        ]
        print(f"⚠️ Auto-configured ALLOWED_HOSTS for Cloud Run service: {cloud_run_service}")
    else:
        raise ImproperlyConfigured(
            "ALLOWED_HOSTS must be explicitly set in production! "
            "Set the ALLOWED_HOSTS environment variable with comma-separated hostnames."
        )
else:
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_STR.split(',') if host.strip()]
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured("ALLOWED_HOSTS cannot be empty in production!")

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
    # Django Security Middleware (must be first)
    'django.middleware.security.SecurityMiddleware',

    # WhiteNoise for static files
    'whitenoise.middleware.WhiteNoiseMiddleware',

    # Custom Security Middleware
    'apps.core.security.middleware.SecurityHeadersMiddleware',
    'apps.core.security.middleware.RateLimitMiddleware',
    'apps.core.security.middleware.SessionSecurityMiddleware',
    'apps.core.security.middleware.AdminProtectionMiddleware',
    'apps.core.security.middleware.RequestLoggingMiddleware',

    # Django Core Middleware
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

if GCS_BUCKET_STATIC:
    # Use GCS for static files
    STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    GS_BUCKET_NAME = GCS_BUCKET_STATIC
    GS_DEFAULT_ACL = 'publicRead'
    STATIC_URL = f'https://storage.googleapis.com/{GCS_BUCKET_STATIC}/'
    print(f"✅ Using GCS for static files: {GCS_BUCKET_STATIC}")
else:
    # Fallback to WhiteNoise - use the correct backend for Django 4.2+
    STORAGES = {
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    STATIC_URL = '/static/'
    print("✅ Using WhiteNoise for static files")

if GCS_BUCKET_MEDIA:
    # Use GCS for media files
    DEFAULT_FILE_STORAGE = 'portfolio.storage_backends.MediaStorage'
    GS_MEDIA_BUCKET_NAME = GCS_BUCKET_MEDIA
    MEDIA_URL = f'https://storage.googleapis.com/{GCS_BUCKET_MEDIA}/'
    print(f"✅ Using GCS for media files: {GCS_BUCKET_MEDIA}")
else:
    # Use local filesystem for media
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
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

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Markdown settings with strict XSS protection
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

# Markdownify settings for XSS prevention with bleach
MARKDOWNIFY = {
    "default": {
        # Whitelist only safe HTML tags
        "WHITELIST_TAGS": [
            'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'code', 'pre', 'blockquote',
            'a', 'strong', 'em', 'hr', 'br', 'table', 'thead',
            'tbody', 'tr', 'th', 'td', 'img', 'span', 'div',
            'sup', 'sub', 'del', 'ins', 'mark', 'abbr'
        ],
        # Whitelist only safe attributes
        "WHITELIST_ATTRS": {
            'a': ['href', 'title', 'rel'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
            'code': ['class'],  # For syntax highlighting
            'pre': ['class'],
            'span': ['class'],  # For inline code
            'div': ['class'],  # For code blocks
        },
        # Whitelist only safe protocols
        "WHITELIST_PROTOCOLS": [
            'http', 'https', 'mailto', 'ftp'
        ],
        # Enable bleach for HTML sanitization
        "BLEACH": True,
        # Strip all comments
        "STRIP_COMMENTS": True,
        # Additional markdown extensions
        "MARKDOWN_EXTENSIONS": [
            'markdown.extensions.fenced_code',
            'markdown.extensions.codehilite',
            'markdown.extensions.tables',
            'markdown.extensions.nl2br',
            'markdown.extensions.toc',
        ],
        # Link handling - add rel="noopener noreferrer" to external links
        "LINKIFY_PARSE_EMAIL": False,  # Don't auto-link emails
        "LINKIFY_SKIP_TAGS": ['pre', 'code'],  # Don't linkify inside code blocks
    }
}

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

# Session security
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookies
SESSION_COOKIE_SAMESITE = 'Strict'  # CSRF protection
SESSION_COOKIE_NAME = 'portfolio_sessionid'  # Custom name to avoid defaults
SESSION_COOKIE_AGE = 86400  # 24 hours (86400 seconds)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True  # Update session expiry on each request
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Use database sessions

# CSRF Protection
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True  # Prevent JavaScript access to CSRF token
CSRF_COOKIE_SAMESITE = 'Strict'  # Additional CSRF protection
CSRF_COOKIE_NAME = 'portfolio_csrftoken'  # Custom name
CSRF_FAILURE_VIEW = 'apps.core.views.csrf_failure'  # Custom CSRF failure page
CSRF_USE_SESSIONS = False  # Use cookies for CSRF tokens (more secure for our use case)

# Security Headers
SECURE_BROWSER_XSS_FILTER = True  # Enable browser's XSS filter (deprecated but harmless)
SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent MIME sniffing
X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'  # Control referrer information

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# Additional Security Headers (requires custom middleware)
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'  # COOP header
SECURE_CROSS_ORIGIN_EMBEDDER_POLICY = 'require-corp'  # COEP header
SECURE_CROSS_ORIGIN_RESOURCE_POLICY = 'same-site'  # CORP header

# Permissions Policy (Feature Policy replacement)
PERMISSIONS_POLICY = {
    'geolocation': 'none',
    'camera': 'none',
    'microphone': 'none',
    'payment': 'none',
    'usb': 'none',
    'magnetometer': 'none',
    'gyroscope': 'none',
    'accelerometer': 'none',
    'ambient-light-sensor': 'none',
    'autoplay': 'self',
    'encrypted-media': 'self',
    'picture-in-picture': 'self',
    'fullscreen': 'self',
}

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

# Security Settings for custom middleware
RATELIMIT_ENABLED = not DEBUG
RATELIMIT_RATE = 100  # requests per minute
RATELIMIT_BLOCK_DURATION = 300  # 5 minutes

# Honeypot settings
HONEYPOT_ENABLED = not DEBUG
HONEYPOT_FIELD_NAME = 'website'  # Field name for honeypot

# Security logging
SECURITY_REQUEST_LOGGING = not DEBUG

# Admin protection
ADMIN_MAX_LOGIN_ATTEMPTS = 5
ADMIN_LOCKOUT_DURATION = 1800  # 30 minutes

# File upload settings
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB

# Password hashers (use Argon2 for better security)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# Login security
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOCKOUT_THRESHOLD = 5
ACCOUNT_LOCKOUT_DURATION = 1800  # 30 minutes

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@example.com')