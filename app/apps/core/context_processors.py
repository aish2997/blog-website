from django.conf import settings
from .models import Profile


def site_settings(request):
    """Add site-wide settings to context"""
    context = {
        'SITE_NAME': settings.SITE_CONFIG.get('name', 'Portfolio'),
        'SITE_DESCRIPTION': settings.SITE_CONFIG.get('description', ''),
        'GITHUB_URL': settings.SITE_CONFIG.get('github_url', ''),
        'LINKEDIN_URL': settings.SITE_CONFIG.get('linkedin_url', ''),
        'TWITTER_URL': settings.SITE_CONFIG.get('twitter_url', ''),
        'CONTACT_EMAIL': settings.SITE_CONFIG.get('email', ''),
    }

    # Try to get profile data if available
    try:
        profile = Profile.objects.first()
        if profile:
            context.update({
                'SITE_NAME': profile.full_name,
                'SITE_DESCRIPTION': profile.title,
                'GITHUB_URL': profile.github_url,
                'LINKEDIN_URL': profile.linkedin_url,
                'TWITTER_URL': profile.twitter_url,
                'CONTACT_EMAIL': profile.email,
                'PROFILE': profile,
            })
    except Exception:
        pass

    return context