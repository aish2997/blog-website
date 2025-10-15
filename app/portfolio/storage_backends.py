"""
Custom storage backends for Google Cloud Storage
"""
from storages.backends.gcloud import GoogleCloudStorage
import os


class MediaStorage(GoogleCloudStorage):
    """Custom storage for media files"""
    bucket_name = os.environ.get('GCS_BUCKET_MEDIA')
    default_acl = 'publicRead'
    file_overwrite = False


class StaticStorage(GoogleCloudStorage):
    """Custom storage for static files"""
    bucket_name = os.environ.get('GCS_BUCKET_STATIC')
    default_acl = 'publicRead'
    file_overwrite = True