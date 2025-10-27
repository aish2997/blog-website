"""
Security middleware for additional protection layers.
"""

import logging
import hashlib
import time
import json
from typing import Optional, Dict, Any
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse


logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to all responses."""

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Add security headers to response."""
        # Content Security Policy
        if not settings.DEBUG:
            csp_directives = {
                'default-src': "'self'",
                'script-src': "'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com",
                'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com",
                'font-src': "'self' https://fonts.gstatic.com data:",
                'img-src': "'self' data: https: http:",
                'connect-src': "'self'",
                'media-src': "'self'",
                'object-src': "'none'",
                'frame-src': "'none'",
                'base-uri': "'self'",
                'form-action': "'self'",
                'frame-ancestors': "'none'",
                'upgrade-insecure-requests': '',
            }

            # Build CSP string
            csp = '; '.join(
                f"{key} {value}" if value else key
                for key, value in csp_directives.items()
            )
            response['Content-Security-Policy'] = csp

        # Additional security headers
        if hasattr(settings, 'SECURE_CROSS_ORIGIN_OPENER_POLICY'):
            response['Cross-Origin-Opener-Policy'] = settings.SECURE_CROSS_ORIGIN_OPENER_POLICY

        if hasattr(settings, 'SECURE_CROSS_ORIGIN_EMBEDDER_POLICY'):
            response['Cross-Origin-Embedder-Policy'] = settings.SECURE_CROSS_ORIGIN_EMBEDDER_POLICY

        if hasattr(settings, 'SECURE_CROSS_ORIGIN_RESOURCE_POLICY'):
            response['Cross-Origin-Resource-Policy'] = settings.SECURE_CROSS_ORIGIN_RESOURCE_POLICY

        # Permissions Policy (Feature Policy replacement)
        if hasattr(settings, 'PERMISSIONS_POLICY'):
            permissions = []
            for feature, policy in settings.PERMISSIONS_POLICY.items():
                if policy == 'none':
                    permissions.append(f"{feature}=()")
                elif policy == 'self':
                    permissions.append(f"{feature}=(self)")
                else:
                    permissions.append(f"{feature}=({policy})")
            response['Permissions-Policy'] = ', '.join(permissions)

        # Additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'  # Legacy but harmless
        response['Referrer-Policy'] = getattr(settings, 'SECURE_REFERRER_POLICY', 'strict-origin-when-cross-origin')

        # Remove server header if possible
        if 'Server' in response:
            del response['Server']

        # Remove X-Powered-By header if present
        if 'X-Powered-By' in response:
            del response['X-Powered-By']

        return response


class RateLimitMiddleware(MiddlewareMixin):
    """Rate limiting middleware for DDoS protection."""

    def __init__(self, get_response):
        """Initialize middleware."""
        self.get_response = get_response
        # Configuration
        self.enabled = getattr(settings, 'RATELIMIT_ENABLED', True)
        self.rate_limit = getattr(settings, 'RATELIMIT_RATE', 100)  # requests per minute
        self.block_duration = getattr(settings, 'RATELIMIT_BLOCK_DURATION', 300)  # 5 minutes

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Check rate limits before processing request."""
        if not self.enabled or settings.DEBUG:
            return None

        # Get client identifier (IP address)
        client_ip = self.get_client_ip(request)
        if not client_ip:
            return None

        # Check if IP is blocked
        block_key = f'ratelimit:blocked:{client_ip}'
        if cache.get(block_key):
            logger.warning(f'Blocked request from {client_ip} (rate limit exceeded)')
            return HttpResponseForbidden('Too many requests. Please try again later.')

        # Check rate limit
        rate_key = f'ratelimit:requests:{client_ip}'
        request_count = cache.get(rate_key, 0)

        if request_count >= self.rate_limit:
            # Block the IP
            cache.set(block_key, True, self.block_duration)
            logger.warning(f'Rate limit exceeded for {client_ip}, blocking for {self.block_duration} seconds')
            return HttpResponseForbidden('Rate limit exceeded. Please try again later.')

        # Increment request count
        cache.set(rate_key, request_count + 1, 60)  # Reset every minute

        return None

    @staticmethod
    def get_client_ip(request: HttpRequest) -> Optional[str]:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RequestLoggingMiddleware(MiddlewareMixin):
    """Log all requests for security monitoring."""

    def __init__(self, get_response):
        """Initialize middleware."""
        self.get_response = get_response
        self.enabled = getattr(settings, 'SECURITY_REQUEST_LOGGING', True)
        self.sensitive_paths = [
            '/admin/',
            '/api/',
            '/login/',
            '/logout/',
            '/password/',
        ]

    def process_request(self, request: HttpRequest) -> None:
        """Log incoming request."""
        if not self.enabled or settings.DEBUG:
            return

        request.security_start_time = time.time()

        # Check if this is a sensitive path
        is_sensitive = any(
            request.path.startswith(path)
            for path in self.sensitive_paths
        )

        if is_sensitive:
            logger.info(
                'Security: Request to sensitive path',
                extra={
                    'path': request.path,
                    'method': request.method,
                    'user': request.user.username if request.user.is_authenticated else 'anonymous',
                    'ip': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                }
            )

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Log response details."""
        if not self.enabled or settings.DEBUG:
            return response

        if hasattr(request, 'security_start_time'):
            duration = time.time() - request.security_start_time

            # Log slow requests
            if duration > 1.0:  # Requests taking more than 1 second
                logger.warning(
                    'Security: Slow request detected',
                    extra={
                        'path': request.path,
                        'duration': duration,
                        'status_code': response.status_code,
                    }
                )

            # Log errors
            if response.status_code >= 400:
                logger.warning(
                    f'Security: HTTP {response.status_code} response',
                    extra={
                        'path': request.path,
                        'method': request.method,
                        'status_code': response.status_code,
                        'user': request.user.username if request.user.is_authenticated else 'anonymous',
                        'ip': self.get_client_ip(request),
                    }
                )

        return response

    @staticmethod
    def get_client_ip(request: HttpRequest) -> Optional[str]:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class HoneypotMiddleware(MiddlewareMixin):
    """Honeypot middleware to detect and block bots."""

    def __init__(self, get_response):
        """Initialize middleware."""
        self.get_response = get_response
        self.honeypot_field = getattr(settings, 'HONEYPOT_FIELD_NAME', 'email_confirm')
        self.enabled = getattr(settings, 'HONEYPOT_ENABLED', True)

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Check for honeypot field in POST requests."""
        if not self.enabled or settings.DEBUG:
            return None

        if request.method == 'POST':
            # Check if honeypot field is filled (should be empty for real users)
            if request.POST.get(self.honeypot_field):
                client_ip = self.get_client_ip(request)
                logger.warning(
                    f'Honeypot triggered: Bot detected from {client_ip}',
                    extra={
                        'ip': client_ip,
                        'path': request.path,
                        'honeypot_value': request.POST.get(self.honeypot_field),
                    }
                )
                # Block the IP for an extended period
                cache.set(f'honeypot:blocked:{client_ip}', True, 86400)  # 24 hours
                return HttpResponseForbidden('Invalid request')

        return None

    @staticmethod
    def get_client_ip(request: HttpRequest) -> Optional[str]:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SessionSecurityMiddleware(MiddlewareMixin):
    """Enhanced session security middleware."""

    def process_request(self, request: HttpRequest) -> None:
        """Add session security checks."""
        if not request.session:
            return

        # Check for session hijacking by verifying user agent
        stored_ua = request.session.get('security_user_agent')
        current_ua = request.META.get('HTTP_USER_AGENT', '')

        if stored_ua and stored_ua != current_ua:
            logger.warning(
                'Possible session hijacking detected',
                extra={
                    'session_id': request.session.session_key,
                    'stored_ua': stored_ua,
                    'current_ua': current_ua,
                    'ip': self.get_client_ip(request),
                }
            )
            # Clear the session
            request.session.flush()
            return

        # Store user agent if not already stored
        if not stored_ua:
            request.session['security_user_agent'] = current_ua

        # Store IP address for session binding
        stored_ip = request.session.get('security_ip')
        current_ip = self.get_client_ip(request)

        if stored_ip and stored_ip != current_ip:
            logger.info(
                'Session IP change detected',
                extra={
                    'session_id': request.session.session_key,
                    'stored_ip': stored_ip,
                    'current_ip': current_ip,
                }
            )
            # You might want to require re-authentication here

        if not stored_ip:
            request.session['security_ip'] = current_ip

    @staticmethod
    def get_client_ip(request: HttpRequest) -> Optional[str]:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AdminProtectionMiddleware(MiddlewareMixin):
    """Extra protection for admin area."""

    def __init__(self, get_response):
        """Initialize middleware."""
        self.get_response = get_response
        self.max_attempts = getattr(settings, 'ADMIN_MAX_LOGIN_ATTEMPTS', 5)
        self.lockout_duration = getattr(settings, 'ADMIN_LOCKOUT_DURATION', 1800)  # 30 minutes

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Check admin area access."""
        if not request.path.startswith('/admin/'):
            return None

        client_ip = self.get_client_ip(request)

        # Check if IP is locked out
        lockout_key = f'admin:lockout:{client_ip}'
        if cache.get(lockout_key):
            logger.warning(f'Admin access blocked for {client_ip} (lockout active)')
            return HttpResponseForbidden('Access temporarily blocked due to multiple failed login attempts.')

        # Track failed login attempts
        if request.path == '/admin/login/' and request.method == 'POST':
            request._admin_login_attempt = True

        return None

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Track admin login attempts."""
        if hasattr(request, '_admin_login_attempt'):
            client_ip = self.get_client_ip(request)

            # Check if login failed (redirect back to login page)
            if response.status_code == 302 and '/admin/login/' in response.url:
                attempts_key = f'admin:attempts:{client_ip}'
                attempts = cache.get(attempts_key, 0) + 1

                if attempts >= self.max_attempts:
                    # Lock out the IP
                    lockout_key = f'admin:lockout:{client_ip}'
                    cache.set(lockout_key, True, self.lockout_duration)
                    logger.warning(f'Admin area locked for {client_ip} after {attempts} failed attempts')
                    cache.delete(attempts_key)
                else:
                    cache.set(attempts_key, attempts, 300)  # Reset after 5 minutes
                    logger.info(f'Failed admin login attempt {attempts}/{self.max_attempts} from {client_ip}')
            else:
                # Successful login, clear attempts
                attempts_key = f'admin:attempts:{client_ip}'
                cache.delete(attempts_key)

        return response

    @staticmethod
    def get_client_ip(request: HttpRequest) -> Optional[str]:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip