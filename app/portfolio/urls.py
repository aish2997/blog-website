"""
URL configuration for portfolio project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.http import JsonResponse

# Health check view for Cloud Run
def health_check(request):
    """Simple health check endpoint for Cloud Run"""
    return JsonResponse({"status": "healthy", "service": "portfolio"}, status=200)

# Customize admin panel
admin.site.site_header = "Portfolio Admin"
admin.site.site_title = "Portfolio Admin"
admin.site.index_title = "Welcome to Your Portfolio Dashboard"

urlpatterns = [
    path('health/', health_check, name='health_check'),  # Health check endpoint
    path('admin/', admin.site.urls),
    path('markdownx/', include('markdownx.urls')),  # For markdown editor

    # django-allauth URLs (Google Sign-In)
    path('accounts/', include('allauth.urls')),

    # App URLs
    path('', include('apps.core.urls')),
    path('blog/', include('apps.blog.urls')),
    path('projects/', include('apps.projects.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
