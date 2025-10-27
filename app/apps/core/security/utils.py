"""
Security utilities for input sanitization and validation.
"""

import re
import html
import bleach
from typing import Any, List, Optional, Dict
from urllib.parse import urlparse, urljoin
from django.conf import settings
from django.utils.html import strip_tags
from django.core.validators import validate_email as django_validate_email
from django.core.exceptions import ValidationError


def sanitize_html(content: str,
                  tags: Optional[List[str]] = None,
                  attrs: Optional[Dict[str, List[str]]] = None,
                  strip: bool = False) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.

    Args:
        content: HTML content to sanitize
        tags: Allowed HTML tags (uses default safe list if None)
        attrs: Allowed attributes for tags
        strip: Whether to strip disallowed tags or escape them

    Returns:
        Sanitized HTML content
    """
    if not content:
        return ''

    # Default safe tags if not specified
    if tags is None:
        tags = [
            'p', 'br', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'a', 'abbr', 'acronym', 'b', 'blockquote',
            'code', 'em', 'i', 'strong', 'pre', 'q', 'small', 'strike',
            'sub', 'sup', 'u', 'hr', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
        ]

    # Default safe attributes if not specified
    if attrs is None:
        attrs = {
            '*': ['class', 'id'],
            'a': ['href', 'title', 'rel'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
            'blockquote': ['cite'],
            'q': ['cite'],
        }

    # Clean with bleach
    cleaned = bleach.clean(
        content,
        tags=tags,
        attributes=attrs,
        strip=strip,
        strip_comments=True
    )

    # Additional safety: remove any javascript: or data: URLs
    cleaned = re.sub(r'(href|src)=["\']?(javascript|data):', r'\1=""', cleaned, flags=re.IGNORECASE)

    return cleaned


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize plain text input.

    Args:
        text: Text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return ''

    # Strip all HTML tags
    text = strip_tags(text)

    # Remove null bytes
    text = text.replace('\x00', '')

    # Normalize whitespace
    text = ' '.join(text.split())

    # Truncate if needed
    if max_length:
        text = text[:max_length]

    return text


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and other attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    if not filename:
        return 'unnamed'

    # Remove path components
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')

    # Remove null bytes
    filename = filename.replace('\x00', '')

    # Keep only alphanumeric, dash, underscore, and dot
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = 250 - len(ext)
        filename = f"{name[:max_name_length]}.{ext}" if ext else name[:255]

    # Don't allow only dots
    if set(filename) == {'.'}:
        filename = 'unnamed'

    return filename


def validate_url(url: str, allowed_hosts: Optional[List[str]] = None) -> bool:
    """
    Validate URL for safety.

    Args:
        url: URL to validate
        allowed_hosts: List of allowed hosts (if None, allows all)

    Returns:
        True if URL is valid and safe
    """
    if not url:
        return False

    try:
        parsed = urlparse(url)

        # Check for dangerous schemes
        if parsed.scheme and parsed.scheme not in ['http', 'https', 'ftp']:
            return False

        # Check for null bytes
        if '\x00' in url:
            return False

        # Check allowed hosts if specified
        if allowed_hosts and parsed.netloc:
            if parsed.netloc not in allowed_hosts:
                return False

        return True
    except Exception:
        return False


def is_safe_redirect_url(url: str, allowed_hosts: Optional[List[str]] = None) -> bool:
    """
    Check if a redirect URL is safe.

    Args:
        url: Redirect URL to check
        allowed_hosts: List of allowed redirect hosts

    Returns:
        True if redirect is safe
    """
    if not url:
        return False

    # Ensure URL is relative or to an allowed host
    parsed = urlparse(url)

    # Relative URLs are safe
    if not parsed.netloc:
        # But check for protocol-relative URLs (//evil.com)
        if url.startswith('//'):
            return False
        return True

    # Check against allowed hosts
    if allowed_hosts:
        return parsed.netloc in allowed_hosts

    # By default, only allow same-origin redirects
    return False


def sanitize_email(email: str) -> Optional[str]:
    """
    Sanitize and validate email address.

    Args:
        email: Email address to sanitize

    Returns:
        Sanitized email or None if invalid
    """
    if not email:
        return None

    # Basic sanitization
    email = email.strip().lower()

    # Remove any HTML tags
    email = strip_tags(email)

    # Validate email format
    try:
        django_validate_email(email)
        return email
    except ValidationError:
        return None


def sanitize_sql_identifier(identifier: str) -> str:
    """
    Sanitize SQL identifier (table/column name).

    Args:
        identifier: SQL identifier to sanitize

    Returns:
        Sanitized identifier
    """
    # Only allow alphanumeric and underscore
    return re.sub(r'[^a-zA-Z0-9_]', '', identifier)


def escape_javascript_string(text: str) -> str:
    """
    Escape string for safe inclusion in JavaScript.

    Args:
        text: Text to escape

    Returns:
        Escaped string safe for JavaScript
    """
    if not text:
        return ''

    # Escape special characters
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    text = text.replace("'", "\\'")
    text = text.replace('\n', '\\n')
    text = text.replace('\r', '\\r')
    text = text.replace('\t', '\\t')
    text = text.replace('</', '<\\/')  # Prevent script tag closing

    return text


def generate_csrf_token() -> str:
    """
    Generate a secure CSRF token.

    Returns:
        CSRF token
    """
    import secrets
    return secrets.token_urlsafe(32)


def constant_time_compare(a: str, b: str) -> bool:
    """
    Constant-time string comparison to prevent timing attacks.

    Args:
        a: First string
        b: Second string

    Returns:
        True if strings are equal
    """
    import hmac
    return hmac.compare_digest(a.encode(), b.encode())


def hash_password(password: str, salt: Optional[str] = None) -> tuple:
    """
    Hash password securely using PBKDF2.

    Args:
        password: Password to hash
        salt: Salt for hashing (generated if None)

    Returns:
        Tuple of (hashed_password, salt)
    """
    import hashlib
    import secrets

    if not salt:
        salt = secrets.token_hex(32)

    # Use PBKDF2 with SHA-256
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt.encode(),
        100000  # iterations
    )

    return hashed.hex(), salt


def generate_secure_filename(original_filename: str) -> str:
    """
    Generate a secure random filename while preserving extension.

    Args:
        original_filename: Original filename

    Returns:
        Secure random filename
    """
    import secrets
    import os

    # Get extension from original filename
    _, ext = os.path.splitext(original_filename)
    ext = sanitize_filename(ext)

    # Generate random filename
    random_name = secrets.token_hex(16)

    return f"{random_name}{ext}"


def rate_limit_key(identifier: str, action: str = 'default') -> str:
    """
    Generate a rate limit cache key.

    Args:
        identifier: User identifier (IP, user ID, etc.)
        action: Action being rate limited

    Returns:
        Cache key for rate limiting
    """
    import hashlib

    # Hash the identifier for privacy
    hashed = hashlib.sha256(f"{identifier}:{action}".encode()).hexdigest()[:16]
    return f"ratelimit:{action}:{hashed}"


def check_password_strength(password: str) -> Dict[str, Any]:
    """
    Check password strength and return detailed analysis.

    Args:
        password: Password to check

    Returns:
        Dictionary with strength analysis
    """
    result = {
        'score': 0,
        'length': len(password),
        'has_lowercase': bool(re.search(r'[a-z]', password)),
        'has_uppercase': bool(re.search(r'[A-Z]', password)),
        'has_digits': bool(re.search(r'\d', password)),
        'has_special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
        'is_common': False,
        'suggestions': []
    }

    # Calculate score
    if result['length'] >= 8:
        result['score'] += 1
    if result['length'] >= 12:
        result['score'] += 1
    if result['has_lowercase']:
        result['score'] += 1
    if result['has_uppercase']:
        result['score'] += 1
    if result['has_digits']:
        result['score'] += 1
    if result['has_special']:
        result['score'] += 1

    # Add suggestions
    if result['length'] < 8:
        result['suggestions'].append('Use at least 8 characters')
    if not result['has_lowercase']:
        result['suggestions'].append('Include lowercase letters')
    if not result['has_uppercase']:
        result['suggestions'].append('Include uppercase letters')
    if not result['has_digits']:
        result['suggestions'].append('Include numbers')
    if not result['has_special']:
        result['suggestions'].append('Include special characters')

    # Check against common passwords (simplified check)
    common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
    if password.lower() in common_passwords:
        result['is_common'] = True
        result['score'] = 0
        result['suggestions'].insert(0, 'This password is too common')

    return result


def obfuscate_email(email: str) -> str:
    """
    Obfuscate email address for display.

    Args:
        email: Email address to obfuscate

    Returns:
        Obfuscated email
    """
    if not email or '@' not in email:
        return '***'

    local, domain = email.split('@', 1)

    # Obfuscate local part
    if len(local) <= 2:
        obfuscated_local = '*' * len(local)
    else:
        obfuscated_local = local[0] + '*' * (len(local) - 2) + local[-1]

    # Partially obfuscate domain
    if '.' in domain:
        domain_parts = domain.split('.')
        domain_parts[0] = domain_parts[0][0] + '*' * (len(domain_parts[0]) - 1)
        obfuscated_domain = '.'.join(domain_parts)
    else:
        obfuscated_domain = domain[0] + '*' * (len(domain) - 1)

    return f"{obfuscated_local}@{obfuscated_domain}"


def get_client_ip(request) -> Optional[str]:
    """
    Get client IP address from Django request.

    Args:
        request: Django request object

    Returns:
        Client IP address or None
    """
    # Check for proxy headers
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP in the chain
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        # Direct connection
        ip = request.META.get('REMOTE_ADDR')

    # Validate IP format
    if ip:
        # Basic validation - you might want to use ipaddress module for thorough validation
        if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', ip):  # IPv4
            return ip
        elif ':' in ip:  # Basic IPv6 check
            return ip

    return None