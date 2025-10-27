"""
Management command for syncing SQLite database with Google Cloud Storage.
This provides data persistence for Cloud Run deployments.
"""
import os
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from google.cloud import storage
from google.cloud.exceptions import NotFound


class Command(BaseCommand):
    help = 'Sync SQLite database with Google Cloud Storage for persistence'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['backup', 'restore', 'auto'],
            default='auto',
            help='Action to perform: backup, restore, or auto (restore then backup)'
        )
        parser.add_argument(
            '--bucket',
            type=str,
            help='GCS bucket name (defaults to media bucket)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force backup even if database hasn\'t changed'
        )

    def handle(self, *args, **options):
        action = options['action']
        bucket_name = options['bucket'] or os.environ.get('GCS_BUCKET_MEDIA')

        if not bucket_name:
            self.stdout.write(self.style.WARNING('No GCS bucket configured. Skipping database sync.'))
            return

        # Database paths
        db_path = settings.DATABASES['default']['NAME']

        if action in ['restore', 'auto']:
            self.restore_database(bucket_name, db_path)

        if action in ['backup', 'auto']:
            self.backup_database(bucket_name, db_path, force=options.get('force', False))

    def restore_database(self, bucket_name, db_path):
        """Restore database from GCS if it exists."""
        try:
            client = storage.Client()
            bucket = client.bucket(bucket_name)

            # Check for existing database backup
            blob = bucket.blob('database-backups/portfolio.sqlite3')

            if blob.exists():
                # Check if local database already exists
                if os.path.exists(db_path):
                    # Compare timestamps if possible
                    backup_time = blob.time_created
                    local_time = datetime.fromtimestamp(os.path.getmtime(db_path), tz=backup_time.tzinfo)

                    if backup_time > local_time:
                        self.stdout.write(self.style.SUCCESS(
                            f'Restoring database from GCS (backup is newer)...'
                        ))
                        # Create backup of current database
                        shutil.copy2(db_path, f'{db_path}.local_backup')
                        # Download from GCS
                        blob.download_to_filename(db_path)
                        self.stdout.write(self.style.SUCCESS('Database restored successfully from GCS'))
                    else:
                        self.stdout.write(self.style.WARNING(
                            'Local database is newer than GCS backup. Skipping restore.'
                        ))
                else:
                    # No local database, download from GCS
                    self.stdout.write(self.style.SUCCESS('Restoring database from GCS...'))
                    os.makedirs(os.path.dirname(db_path), exist_ok=True)
                    blob.download_to_filename(db_path)
                    self.stdout.write(self.style.SUCCESS('Database restored successfully from GCS'))
            else:
                self.stdout.write(self.style.WARNING('No database backup found in GCS'))

        except NotFound:
            self.stdout.write(self.style.WARNING(f'Bucket {bucket_name} not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error restoring database: {e}'))

    def backup_database(self, bucket_name, db_path, force=False):
        """Backup database to GCS."""
        try:
            # Check if database exists
            if not os.path.exists(db_path):
                self.stdout.write(self.style.WARNING('No database to backup'))
                return

            client = storage.Client()
            bucket = client.bucket(bucket_name)

            # Main backup
            blob = bucket.blob('database-backups/portfolio.sqlite3')

            # Check if backup is needed
            if not force and blob.exists():
                # Compare file sizes or checksums
                local_size = os.path.getsize(db_path)
                remote_size = blob.size

                if local_size == remote_size:
                    self.stdout.write(self.style.WARNING(
                        'Database unchanged, skipping backup (use --force to override)'
                    ))
                    return

            # Perform backup
            self.stdout.write(self.style.SUCCESS('Backing up database to GCS...'))
            blob.upload_from_filename(db_path)

            # Also create a timestamped backup (keep last 5)
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            timestamped_blob = bucket.blob(f'database-backups/archive/portfolio_{timestamp}.sqlite3')
            timestamped_blob.upload_from_filename(db_path)

            # Clean up old timestamped backups (keep only last 5)
            self.cleanup_old_backups(bucket)

            self.stdout.write(self.style.SUCCESS('Database backed up successfully to GCS'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error backing up database: {e}'))

    def cleanup_old_backups(self, bucket):
        """Keep only the last 5 timestamped backups."""
        try:
            # List all timestamped backups
            blobs = list(bucket.list_blobs(prefix='database-backups/archive/'))

            # Sort by creation time
            blobs.sort(key=lambda x: x.time_created, reverse=True)

            # Delete old backups (keep last 5)
            if len(blobs) > 5:
                for blob in blobs[5:]:
                    blob.delete()
                    self.stdout.write(self.style.WARNING(f'Deleted old backup: {blob.name}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error cleaning up old backups: {e}'))