from django.apps import AppConfig
from django.db import connection
from django.db.backends.signals import connection_created
import logging

logger = logging.getLogger(__name__)


def optimize_sqlite(sender, connection, **kwargs):
    """
    Apply SQLite performance optimizations after connection is created.
    These PRAGMA commands improve SQLite performance significantly.
    """
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        try:
            # Apply performance optimizations
            pragma_commands = [
                "PRAGMA journal_mode=WAL;",  # Write-Ahead Logging for better concurrency
                "PRAGMA synchronous=NORMAL;",  # Faster writes with reasonable safety
                "PRAGMA cache_size=10000;",  # Increase cache size (pages)
                "PRAGMA temp_store=MEMORY;",  # Use memory for temporary tables
            ]

            for command in pragma_commands:
                cursor.execute(command)
                logger.info(f"SQLite optimization applied: {command}")

        except Exception as e:
            logger.warning(f"Failed to apply SQLite optimizations: {e}")
        finally:
            cursor.close()


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'

    def ready(self):
        """Connect the SQLite optimization signal when app is ready."""
        # Only connect the signal once
        if not hasattr(self, '_signal_connected'):
            connection_created.connect(optimize_sqlite)
            self._signal_connected = True
            logger.info("SQLite optimization signal connected")
