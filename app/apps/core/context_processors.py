import os
import logging
from django.conf import settings
from .models import Profile

logger = logging.getLogger(__name__)


def site_settings(request):
    """Add site-wide settings to context with proper error handling"""
    context = {}

    try:
        # Only try to get profile if database is ready
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")  # Test database connection

        profile = Profile.objects.first()
        if profile:
            context.update({
                'SITE_NAME': profile.full_name or os.environ.get('SITE_NAME', 'Portfolio'),
                'SITE_DESCRIPTION': profile.title or os.environ.get('SITE_DESCRIPTION', 'Full Stack Developer'),
                'GITHUB_URL': profile.github_url or os.environ.get('GITHUB_URL', '#'),
                'LINKEDIN_URL': profile.linkedin_url or os.environ.get('LINKEDIN_URL', '#'),
                'TWITTER_URL': profile.twitter_url or os.environ.get('TWITTER_URL', '#'),
                'CONTACT_EMAIL': profile.email or os.environ.get('EMAIL_CONTACT', ''),
                'PROFILE': profile,
            })
        else:
            # Provide defaults if no profile exists
            context.update({
                'SITE_NAME': os.environ.get('SITE_NAME', 'Portfolio'),
                'SITE_DESCRIPTION': os.environ.get('SITE_DESCRIPTION', 'Full Stack Developer'),
                'PROFILE': None,
            })
    except Exception as e:
        # Log the error but provide defaults
        logger.warning(f"Could not load site context: {e}")
        context.update({
            'SITE_NAME': os.environ.get('SITE_NAME', 'Portfolio'),
            'SITE_DESCRIPTION': os.environ.get('SITE_DESCRIPTION', 'Full Stack Developer'),
            'PROFILE': None,
        })

    # Always add these from environment/settings
    context.update({
        'GITHUB_URL': context.get('GITHUB_URL') or os.environ.get('GITHUB_URL', '#'),
        'LINKEDIN_URL': context.get('LINKEDIN_URL') or os.environ.get('LINKEDIN_URL', '#'),
        'TWITTER_URL': context.get('TWITTER_URL') or os.environ.get('TWITTER_URL', '#'),
        'CONTACT_EMAIL': context.get('CONTACT_EMAIL') or os.environ.get('EMAIL_CONTACT', ''),
        'GA4_MEASUREMENT_ID': os.environ.get('GA4_MEASUREMENT_ID', ''),  # Google Analytics 4
    })

    # Try to get from settings.SITE_CONFIG if it exists
    if hasattr(settings, 'SITE_CONFIG'):
        for key, value in settings.SITE_CONFIG.items():
            env_key = key.upper()
            if env_key not in context or not context[env_key]:
                context[env_key] = value

    return context