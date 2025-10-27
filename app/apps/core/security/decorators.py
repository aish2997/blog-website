"""
Security decorators for views and functions.
"""

import functools
import hashlib
import time
from typing import Callable, Optional, Any
from django.http import HttpRequest, HttpResponseForbidden, JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect


def rate_limit(key: str = 'ip',
               rate: str = '10/m',
               method: str = 'ALL',
               block_duration: int = 300) -> Callable:
    """
    Rate limit decorator for views.

    Args:
        key: What to use as rate limit key ('ip', 'user', 'session')
        rate: Rate limit (e.g., '10/m' for 10 per minute, '100/h' for 100 per hour)
        method: HTTP method to limit ('ALL', 'GET', 'POST', etc.)
        block_duration: How long to block after exceeding limit (seconds)

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
            # Check if rate limiting is enabled
            if settings.DEBUG or not getattr(settings, 'RATELIMIT_ENABLED', True):
                return func(request, *args, **kwargs)

            # Check method
            if method != 'ALL' and request.method != method:
                return func(request, *args, **kwargs)

            # Get identifier based on key type
            if key == 'ip':
                identifier = get_client_ip(request)
            elif key == 'user':
                if not request.user.is_authenticated:
                    return func(request, *args, **kwargs)
                identifier = str(request.user.id)
            elif key == 'session':
                if not request.session.session_key:
                    return func(request, *args, **kwargs)
                identifier = request.session.session_key
            else:
                identifier = str(key)

            # Parse rate limit
            limit, period = rate.split('/')
            limit = int(limit)

            if period == 's':
                duration = 1
            elif period == 'm':
                duration = 60
            elif period == 'h':
                duration = 3600
            elif period == 'd':
                duration = 86400
            else:
                duration = int(period)

            # Generate cache keys
            cache_key = f'ratelimit:{func.__name__}:{identifier}'
            block_key = f'ratelimit:block:{func.__name__}:{identifier}'

            # Check if blocked
            if cache.get(block_key):
                return HttpResponseForbidden('Rate limit exceeded. Please try again later.')

            # Get current count
            count = cache.get(cache_key, 0)

            if count >= limit:
                # Block the identifier
                cache.set(block_key, True, block_duration)
                return HttpResponseForbidden('Rate limit exceeded. Please try again later.')

            # Increment count
            cache.set(cache_key, count + 1, duration)

            return func(request, *args, **kwargs)

        return wrapper
    return decorator


def require_https(func: Callable) -> Callable:
    """
    Require HTTPS for the decorated view.

    Args:
        func: View function to decorate

    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
        if not request.is_secure() and not settings.DEBUG:
            # Redirect to HTTPS version
            return redirect(f'https://{request.get_host()}{request.get_full_path()}')
        return func(request, *args, **kwargs)
    return wrapper


def ajax_required(func: Callable) -> Callable:
    """
    Require request to be AJAX.

    Args:
        func: View function to decorate

    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return HttpResponseForbidden('AJAX request required')
        return func(request, *args, **kwargs)
    return wrapper


def staff_required(func: Callable) -> Callable:
    """
    Require user to be staff.

    Args:
        func: View function to decorate

    Returns:
        Decorated function
    """
    @functools.wraps(func)
    @user_passes_test(lambda u: u.is_staff)
    def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
        return func(request, *args, **kwargs)
    return wrapper


def superuser_required(func: Callable) -> Callable:
    """
    Require user to be superuser.

    Args:
        func: View function to decorate

    Returns:
        Decorated function
    """
    @functools.wraps(func)
    @user_passes_test(lambda u: u.is_superuser)
    def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
        return func(request, *args, **kwargs)
    return wrapper


def log_security_event(event_type: str) -> Callable:
    """
    Log security events for monitoring.

    Args:
        event_type: Type of security event

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
            import logging
            logger = logging.getLogger('security')

            # Log the security event
            logger.info(
                f'Security Event: {event_type}',
                extra={
                    'event_type': event_type,
                    'function': func.__name__,
                    'user': request.user.username if request.user.is_authenticated else 'anonymous',
                    'ip': get_client_ip(request),
                    'path': request.path,
                    'method': request.method,
                }
            )

            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def validate_referer(allowed_hosts: Optional[list] = None) -> Callable:
    """
    Validate HTTP referer header.

    Args:
        allowed_hosts: List of allowed referer hosts

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
            referer = request.META.get('HTTP_REFERER')

            if referer:
                from urllib.parse import urlparse
                parsed = urlparse(referer)
                referer_host = parsed.netloc

                # Check against allowed hosts
                hosts = allowed_hosts or [request.get_host()]
                if referer_host not in hosts:
                    return HttpResponseForbidden('Invalid referer')

            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def honeypot(field_name: str = 'email_confirm') -> Callable:
    """
    Honeypot field to catch bots.

    Args:
        field_name: Name of honeypot field

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
            if request.method == 'POST':
                # Check if honeypot field is filled
                if request.POST.get(field_name):
                    # Bot detected
                    import logging
                    logger = logging.getLogger('security')
                    logger.warning(
                        f'Honeypot triggered: Bot detected',
                        extra={
                            'ip': get_client_ip(request),
                            'path': request.path,
                            'honeypot_field': field_name,
                            'honeypot_value': request.POST.get(field_name)[:100],
                        }
                    )
                    # Block the IP
                    ip = get_client_ip(request)
                    if ip:
                        cache.set(f'honeypot:blocked:{ip}', True, 86400)  # 24 hours
                    return HttpResponseForbidden('Invalid request')

            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def secure_headers(func: Callable) -> Callable:
    """
    Add security headers to response.

    Args:
        func: View function to decorate

    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
        response = func(request, *args, **kwargs)

        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Remove server information
        if 'Server' in response:
            del response['Server']
        if 'X-Powered-By' in response:
            del response['X-Powered-By']

        return response
    return wrapper


def timing_safe(func: Callable) -> Callable:
    """
    Make function timing-safe to prevent timing attacks.

    Args:
        func: Function to make timing-safe

    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        import random
        import time

        # Add random delay to prevent timing attacks
        delay = random.uniform(0.001, 0.005)  # 1-5ms random delay
        time.sleep(delay)

        return func(*args, **kwargs)
    return wrapper


def sanitize_output(func: Callable) -> Callable:
    """
    Sanitize function output to prevent XSS.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        from django.utils.html import escape
        result = func(*args, **kwargs)

        # Sanitize string output
        if isinstance(result, str):
            return escape(result)

        # Sanitize dict output
        if isinstance(result, dict):
            return {k: escape(v) if isinstance(v, str) else v for k, v in result.items()}

        # Sanitize list output
        if isinstance(result, list):
            return [escape(item) if isinstance(item, str) else item for item in result]

        return result
    return wrapper


def cache_control(max_age: int = 0,
                 no_cache: bool = False,
                 no_store: bool = False,
                 must_revalidate: bool = False,
                 private: bool = False) -> Callable:
    """
    Set cache control headers.

    Args:
        max_age: Max age in seconds
        no_cache: Disable caching
        no_store: Don't store in cache
        must_revalidate: Must revalidate with server
        private: Private cache only

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
            response = func(request, *args, **kwargs)

            cache_control = []

            if no_cache:
                cache_control.append('no-cache')
            if no_store:
                cache_control.append('no-store')
            if must_revalidate:
                cache_control.append('must-revalidate')
            if private:
                cache_control.append('private')
            else:
                cache_control.append('public')

            cache_control.append(f'max-age={max_age}')

            response['Cache-Control'] = ', '.join(cache_control)

            return response
        return wrapper
    return decorator


def get_client_ip(request: HttpRequest) -> Optional[str]:
    """
    Get client IP address from request.

    Args:
        request: Django request object

    Returns:
        Client IP address or None
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Composite decorators for common use cases
secure_api = functools.partial(
    lambda func: never_cache(
        csrf_protect(
            secure_headers(
                rate_limit(rate='30/m')(func)
            )
        )
    )
)

secure_admin = functools.partial(
    lambda func: staff_required(
        log_security_event('admin_access')(
            secure_headers(
                rate_limit(rate='20/m')(func)
            )
        )
    )
)