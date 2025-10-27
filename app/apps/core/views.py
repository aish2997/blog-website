from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView, View
from .models import (
    Profile, Skill, Education, WorkExperience,
    Certification, Achievement, CVDownload
)
from apps.blog.models import BlogPost
from apps.projects.models import Project
from apps.analytics.models import Visitor


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
