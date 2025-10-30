from django.apps import AppConfig


class CommentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.comments'

    def ready(self):
        """Import signals when the app is ready."""
        import apps.comments.signals  # noqa
