"""
Custom middleware for handling admin-specific security configurations.

This middleware provides granular control over security headers, applying
relaxed settings for admin routes while maintaining strict security for
public-facing pages.
"""

from django.conf import settings
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class AdminSecurityMiddleware(MiddlewareMixin):
    """
    Middleware to apply different security headers for admin and public pages.

    This ensures the Django admin panel functions properly while maintaining
    strong security for public-facing pages.
    """

    # Admin URL patterns that need relaxed security
    ADMIN_PATTERNS = [
        '/admin/',
        '/markdownx/',  # Markdown editor used in admin
    ]

    def process_response(self, request, response):
        """
        Modify security headers based on the request path.

        Args:
            request: The HTTP request object
            response: The HTTP response object

        Returns:
            The modified response object
        """
        # Check if this is an admin request
        is_admin_request = any(
            request.path.startswith(pattern)
            for pattern in self.ADMIN_PATTERNS
        )

        if is_admin_request:
            # Apply relaxed security headers for admin
            # SAMEORIGIN allows the site to frame itself (needed for admin functionality)
            response['X-Frame-Options'] = 'SAMEORIGIN'

            # Remove overly restrictive CSP if it exists (admin needs inline scripts/styles)
            if 'Content-Security-Policy' in response:
                del response['Content-Security-Policy']

            # Allow admin to work properly with its inline styles and scripts
            # But still maintain XSS protection
            response['X-Content-Type-Options'] = 'nosniff'

            # Log in debug mode for troubleshooting
            if settings.DEBUG:
                response['X-Admin-Request'] = 'true'

        else:
            # Apply strict security headers for public pages
            # These settings provide maximum security for public-facing content

            # Prevent clickjacking attacks
            response['X-Frame-Options'] = getattr(settings, 'X_FRAME_OPTIONS', 'DENY')

            # Prevent MIME type sniffing
            response['X-Content-Type-Options'] = 'nosniff'

            # Enable browser XSS protection (legacy but still useful)
            response['X-XSS-Protection'] = '1; mode=block'

            # Apply CSP if configured (can be customized per deployment)
            csp = getattr(settings, 'CONTENT_SECURITY_POLICY', None)
            if csp:
                response['Content-Security-Policy'] = csp

            # Additional security headers for production
            if not settings.DEBUG:
                # HTTP Strict Transport Security (only in production with HTTPS)
                if getattr(settings, 'SECURE_SSL_REDIRECT', False):
                    max_age = getattr(settings, 'SECURE_HSTS_SECONDS', 31536000)
                    response['Strict-Transport-Security'] = f'max-age={max_age}; includeSubDomains; preload'

                # Referrer Policy for privacy
                response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

                # Permissions Policy (replaces Feature Policy)
                response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        return response


class AdminStaticFilesMiddleware(MiddlewareMixin):
    """
    Middleware to ensure admin static files are properly served.

    This middleware adds cache headers and ensures admin resources
    are accessible even with strict security settings.
    """

    def process_response(self, request, response):
        """
        Add appropriate cache headers for admin static files.

        Args:
            request: The HTTP request object
            response: The HTTP response object

        Returns:
            The modified response object
        """
        # Check if this is an admin static file request
        if request.path.startswith('/static/admin/'):
            # Set cache headers for admin static files
            # Cache for 1 hour in development, 1 day in production
            cache_timeout = 3600 if settings.DEBUG else 86400
            response['Cache-Control'] = f'public, max-age={cache_timeout}'

            # Ensure CORS is allowed for admin static files if needed
            # This helps when admin is served from a different domain/subdomain
            if hasattr(settings, 'ADMIN_CORS_ORIGIN'):
                response['Access-Control-Allow-Origin'] = settings.ADMIN_CORS_ORIGIN

        return response


class HealthCheckMiddleware(MiddlewareMixin):
    """
    Middleware to handle health check endpoints for monitoring.

    This is useful for load balancers and monitoring systems.
    """

    HEALTH_CHECK_PATHS = [
        '/_health',
        '/health',
        '/healthz',
    ]

    def process_request(self, request):
        """
        Handle health check requests without going through full Django stack.

        Args:
            request: The HTTP request object

        Returns:
            HttpResponse for health checks, None otherwise
        """
        if request.path in self.HEALTH_CHECK_PATHS:
            from django.http import HttpResponse
            return HttpResponse('OK', content_type='text/plain')
        return None