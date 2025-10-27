from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView, View
from django.views.decorators.csrf import requires_csrf_token
from .models import (
    Profile, Skill, Education, WorkExperience,
    Certification, Achievement, CVDownload
)
from apps.blog.models import BlogPost
from apps.projects.models import Project
from apps.analytics.models import Visitor
import logging

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    """Homepage view"""
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Track visitor (session-based to prevent refresh increments)
        visitor_ip = self.request.META.get('REMOTE_ADDR')
        session_key = f'visitor_tracked_{visitor_ip}'

        # Check if visitor has been tracked in this session
        if visitor_ip and not self.request.session.get(session_key):
            Visitor.objects.get_or_create(
                ip_address=visitor_ip,
                defaults={'user_agent': self.request.META.get('HTTP_USER_AGENT', '')}
            )
            # Mark visitor as tracked for this session
            self.request.session[session_key] = True
            self.request.session.set_expiry(86400)  # Expire after 24 hours

        # Get profile
        context['profile'] = Profile.objects.first()

        # Get featured content
        context['featured_posts'] = BlogPost.objects.filter(
            status='published', is_featured=True
        ).order_by('-published_date')[:3]

        context['featured_projects'] = Project.objects.filter(
            is_public=True, featured=True
        )[:3]

        # Get stats
        context['total_posts'] = BlogPost.objects.filter(status='published').count()
        context['total_projects'] = Project.objects.filter(is_public=True).count()
        context['total_visitors'] = Visitor.objects.count()

        return context


class CVView(TemplateView):
    """CV/Resume view"""
    template_name = 'core/cv.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get profile data
        profile = Profile.objects.first()
        context['profile'] = profile

        # Get CV view count from CVDownload
        cv_download = CVDownload.objects.filter(is_active=True).first()
        context['cv_views'] = cv_download.view_count if cv_download else 0

        # Get all CV data
        context['skills'] = Skill.objects.all().order_by('skill_type', 'order')
        context['education'] = Education.objects.all().order_by('-end_date')
        context['experience'] = WorkExperience.objects.all().order_by('-end_date')
        context['certifications'] = Certification.objects.all().order_by('-issue_date')
        context['achievements'] = Achievement.objects.all().order_by('-date')

        # Get skill categories
        skill_categories = {}
        for skill in context['skills']:
            if skill.skill_type not in skill_categories:
                skill_categories[skill.skill_type] = []
            skill_categories[skill.skill_type].append(skill)
        context['skill_categories'] = skill_categories

        return context


class CVDownloadView(View):
    """Handle CV PDF downloads"""

    def get(self, request):
        """Handle CV download with proper storage backend support"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            cv_download = CVDownload.objects.filter(is_active=True).first()

            if not cv_download or not cv_download.file:
                # If no CV file, redirect to CV page
                return redirect('core:cv')

            # Track download
            cv_download.increment_download_count()

            # Handle both local and cloud storage
            try:
                # Try to read the file directly (works for both local and GCS)
                file_content = cv_download.file.read()
                response = HttpResponse(file_content, content_type='application/pdf')
                filename = f"CV_{cv_download.version}.pdf"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
            except Exception as e:
                # If direct read fails, try URL redirect (for GCS public URLs)
                if hasattr(cv_download.file, 'url'):
                    return redirect(cv_download.file.url)
                logger.error(f"Could not access CV file: {e}")
                return redirect('core:cv')

        except Exception as e:
            logger.error(f"Error in CVDownloadView: {e}")
            return redirect('core:cv')


class HealthCheckView(View):
    """Health check endpoint for monitoring"""

    def get(self, request):
        try:
            # Test database connection
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")

            return JsonResponse({
                'status': 'healthy',
                'service': 'portfolio',
                'database': 'connected'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'unhealthy',
                'error': str(e)
            }, status=503)


@requires_csrf_token
def csrf_failure(request, reason=""):
    """
    Custom CSRF failure view for better user experience and security logging.
    """
    # Log the CSRF failure for security monitoring
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '')
    logger.warning(
        f'CSRF verification failed',
        extra={
            'reason': reason,
            'path': request.path,
            'method': request.method,
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
            'ip': client_ip,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
        }
    )

    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'CSRF verification failed',
            'message': 'Your session may have expired. Please refresh the page and try again.'
        }, status=403)

    # Render a user-friendly error page
    context = {
        'title': 'Security Verification Failed',
        'message': 'We couldn\'t verify your request for security reasons.',
        'reason': reason,
        'suggestions': [
            'Your session may have expired. Please refresh the page and try again.',
            'Make sure cookies are enabled in your browser.',
            'If you\'re using a bookmark, please visit the homepage first.',
            'Clear your browser cache and cookies for this site.',
        ],
        'is_csrf_failure': True,
    }

    # Try to use a custom template if available
    try:
        return render(request, 'core/csrf_failure.html', context, status=403)
    except:
        # Fallback to a simple response if template doesn't exist
        return HttpResponse(
            f"""
            <html>
            <head>
                <title>Security Verification Failed</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                        max-width: 600px;
                        margin: 50px auto;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        background: white;
                        padding: 40px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    h1 {{
                        color: #d32f2f;
                        margin-bottom: 20px;
                    }}
                    ul {{
                        line-height: 1.8;
                        color: #555;
                    }}
                    .button {{
                        display: inline-block;
                        margin-top: 20px;
                        padding: 10px 20px;
                        background-color: #1976d2;
                        color: white;
                        text-decoration: none;
                        border-radius: 4px;
                    }}
                    .button:hover {{
                        background-color: #1565c0;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Security Verification Failed</h1>
                    <p>We couldn't verify your request for security reasons.</p>
                    <h3>What you can do:</h3>
                    <ul>
                        <li>Refresh the page and try again</li>
                        <li>Make sure cookies are enabled in your browser</li>
                        <li>Clear your browser cache and cookies for this site</li>
                        <li>If the problem persists, try using a different browser</li>
                    </ul>
                    <a href="/" class="button">Go to Homepage</a>
                </div>
            </body>
            </html>
            """,
            content_type='text/html',
            status=403
        )
