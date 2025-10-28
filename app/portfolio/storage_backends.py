"""
Custom storage backends for Google Cloud Storage
"""
from django.core.exceptions import ImproperlyConfigured
from storages.backends.gcloud import GoogleCloudStorage
import os


class MediaStorage(GoogleCloudStorage):
    """Custom storage for media files"""
    bucket_name = os.environ.get('GCS_BUCKET_MEDIA')
    # Don't set ACL - bucket has uniform access control
    default_acl = None
    file_overwrite = False
    # Ensure we're not trying to set individual object permissions
    querystring_auth = False

    def __init__(self, **kwargs):
        if not self.bucket_name:
            raise ImproperlyConfigured(
                "GCS_BUCKET_MEDIA environment variable is required for MediaStorage"
            )
        super().__init__(**kwargs)


class StaticStorage(GoogleCloudStorage):
    """Custom storage for static files"""
    bucket_name = os.environ.get('GCS_BUCKET_STATIC')
    # Don't set ACL - bucket has uniform access control
    default_acl = None
    file_overwrite = True
    # Ensure we're not trying to set individual object permissions
    querystring_auth = False

    def __init__(self, **kwargs):
        if not self.bucket_name:
            raise ImproperlyConfigured(
                "GCS_BUCKET_STATIC environment variable is required for StaticStorage"
            )
        super().__init__(**kwargs)