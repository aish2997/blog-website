from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    Profile, Skill, Education, WorkExperience,
    Certification, Achievement, CVDownload
)
from apps.blog.models import BlogPost
from apps.projects.models import Project


class HomeView(TemplateView):
    """Homepage view"""
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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

        # Get skills for display
        skills = Skill.objects.all().order_by('skill_type', 'order')
        skill_categories = {}
        for skill in skills:
            if skill.skill_type not in skill_categories:
                skill_categories[skill.skill_type] = []
            skill_categories[skill.skill_type].append(skill)
        context['skill_categories'] = skill_categories

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

        # Track CV views (once per session per 24 hours)
        if cv_download:
            session_key = f'cv_viewed_{cv_download.id}'
            if not self.request.session.get(session_key):
                cv_download.increment_view_count()
                self.request.session[session_key] = True
                self.request.session.set_expiry(86400)  # Expire after 24 hours

        context['cv_views'] = cv_download.view_count if cv_download else 0
        context['cv_downloads'] = cv_download.download_count if cv_download else 0

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


class CVDownloadView(LoginRequiredMixin, View):
    """Handle CV PDF downloads - requires Google authentication"""
    login_url = '/accounts/login/'

    def get(self, request):
        """Handle CV download with authentication and email notification"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            cv_download = CVDownload.objects.filter(is_active=True).first()

            if not cv_download or not cv_download.file:
                messages.error(request, 'CV file not available.')
                return redirect('core:cv')

            # Get user information
            user = request.user
            user_name = user.get_full_name() or user.username
            user_email = user.email

            # Get profile picture from Google OAuth if available
            profile_picture_url = ''
            try:
                social_account = user.socialaccount_set.filter(provider='google').first()
                if social_account and social_account.extra_data:
                    profile_picture_url = social_account.extra_data.get('picture', '')
            except Exception:
                pass

            # Track download
            cv_download.increment_download_count()

            # Send email notification to site owner
            try:
                from django.utils import timezone
                download_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

                email_subject = f'Resume Downloaded by {user_name}'
                email_body = f"""
Hello,

Your resume has been downloaded!

Downloaded by: {user_name}
Email: {user_email}
Time: {download_time}
Total Downloads: {cv_download.download_count}

User Profile Picture: {profile_picture_url if profile_picture_url else 'N/A'}

---
This is an automated notification from your portfolio website.
                """.strip()

                # Send email (make sure to configure email settings)
                recipient_email = getattr(settings, 'ADMIN_EMAIL', getattr(settings, 'CONTACT_EMAIL', None))

                if recipient_email:
                    send_mail(
                        subject=email_subject,
                        message=email_body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[recipient_email],
                        fail_silently=True,  # Don't break download if email fails
                    )
                    logger.info(f"Email notification sent for CV download by {user_email}")
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")
                # Continue with download even if email fails

            # Handle both local and cloud storage
            try:
                # Try to read the file directly (works for both local and GCS)
                file_content = cv_download.file.read()
                response = HttpResponse(file_content, content_type='application/pdf')
                filename = f"CV_{cv_download.version}.pdf"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'

                # Add success message
                messages.success(request, f'Resume downloaded successfully! Thank you, {user_name}.')

                return response
            except Exception as e:
                # If direct read fails, try URL redirect (for GCS public URLs)
                if hasattr(cv_download.file, 'url'):
                    messages.success(request, f'Resume downloaded successfully! Thank you, {user_name}.')
                    return redirect(cv_download.file.url)
                logger.error(f"Could not access CV file: {e}")
                messages.error(request, 'Error accessing CV file.')
                return redirect('core:cv')

        except Exception as e:
            logger.error(f"Error in CVDownloadView: {e}")
            messages.error(request, 'An error occurred while downloading the resume.')
            return redirect('core:cv')


class HealthCheckView(View):
    """Health check endpoint for monitoring"""

    def get(self, request):
        import os
        from django.conf import settings

        health_status = {
            'status': 'healthy',
            'service': 'portfolio',
            'checks': {}
        }
        is_healthy = True

        # Test database connection
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status['checks']['database'] = 'connected'
        except Exception as e:
            health_status['checks']['database'] = f'error: {str(e)}'
            is_healthy = False

        # Test static files (especially admin CSS)
        try:
            static_root = settings.STATIC_ROOT
            admin_css_path = os.path.join(static_root, 'admin', 'css', 'base.css')
            if os.path.exists(admin_css_path):
                health_status['checks']['admin_static'] = 'present'
            else:
                health_status['checks']['admin_static'] = 'missing'
                # Don't mark as unhealthy, just warn
        except Exception as e:
            health_status['checks']['admin_static'] = f'error: {str(e)}'

        # Test media directory access
        try:
            media_root = settings.MEDIA_ROOT
            if os.path.exists(media_root):
                health_status['checks']['media_directory'] = 'accessible'
            else:
                # Try to create it
                os.makedirs(media_root, exist_ok=True)
                health_status['checks']['media_directory'] = 'created'
        except Exception as e:
            health_status['checks']['media_directory'] = f'error: {str(e)}'

        # Check for critical settings
        try:
            secret_key_set = bool(settings.SECRET_KEY and len(settings.SECRET_KEY) > 40)
            health_status['checks']['secret_key'] = 'configured' if secret_key_set else 'missing'
            if not secret_key_set:
                is_healthy = False
        except:
            health_status['checks']['secret_key'] = 'error'
            is_healthy = False

        # Overall status
        health_status['status'] = 'healthy' if is_healthy else 'unhealthy'

        # Return appropriate status code
        status_code = 200 if is_healthy else 503
        return JsonResponse(health_status, status=status_code)
