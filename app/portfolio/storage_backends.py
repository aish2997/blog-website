"""
Custom storage backends for Google Cloud Storage
"""
from django.core.exceptions import ImproperlyConfigured
from storages.backends.gcloud import GoogleCloudStorage
import os


class MediaStorage(GoogleCloudStorage):
    """Custom storage for media files"""
    default_acl = 'publicRead'
    file_overwrite = False

    def __init__(self, **kwargs):
        # bucket_name will be passed via OPTIONS in STORAGES setting
        if 'bucket_name' not in kwargs and not os.environ.get('GCS_BUCKET_MEDIA'):
            raise ImproperlyConfigured(
                "GCS_BUCKET_MEDIA environment variable or bucket_name parameter is required for MediaStorage"
            )
        # If bucket_name not in kwargs, try to get from env
        if 'bucket_name' not in kwargs:
            kwargs['bucket_name'] = os.environ.get('GCS_BUCKET_MEDIA')
        super().__init__(**kwargs)


class StaticStorage(GoogleCloudStorage):
    """Custom storage for static files"""
    default_acl = 'publicRead'
    file_overwrite = True

    def __init__(self, **kwargs):
        # bucket_name will be passed via OPTIONS in STORAGES setting
        if 'bucket_name' not in kwargs and not os.environ.get('GCS_BUCKET_STATIC'):
            raise ImproperlyConfigured(
                "GCS_BUCKET_STATIC environment variable or bucket_name parameter is required for StaticStorage"
            )
        # If bucket_name not in kwargs, try to get from env
        if 'bucket_name' not in kwargs:
            kwargs['bucket_name'] = os.environ.get('GCS_BUCKET_STATIC')
        super().__init__(**kwargs)