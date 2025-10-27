"""
File upload validators and security checks.
"""

import os
import magic
import hashlib
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from typing import Any, List, Optional


class FileSizeValidator:
    """Validates file size doesn't exceed maximum limit."""

    def __init__(self, max_size: int):
        """
        Initialize validator.

        Args:
            max_size: Maximum file size in bytes
        """
        self.max_size = max_size

    def __call__(self, value: Any) -> None:
        """Validate file size."""
        filesize = value.size
        if filesize > self.max_size:
            raise ValidationError(
                _('File size cannot exceed %(max_size)s MB.'),
                params={'max_size': self.max_size / (1024 * 1024)},
            )


class MimeTypeValidator:
    """Validates file MIME type for security."""

    def __init__(self, allowed_types: List[str]):
        """
        Initialize validator.

        Args:
            allowed_types: List of allowed MIME types
        """
        self.allowed_types = allowed_types

    def __call__(self, value: Any) -> None:
        """Validate file MIME type using python-magic."""
        try:
            # Read first 2048 bytes for MIME detection
            file_content = value.read(2048)
            value.seek(0)  # Reset file pointer

            # Detect MIME type
            mime = magic.from_buffer(file_content, mime=True)

            if mime not in self.allowed_types:
                raise ValidationError(
                    _('File type "%(mime)s" is not allowed. Allowed types: %(allowed)s'),
                    params={
                        'mime': mime,
                        'allowed': ', '.join(self.allowed_types)
                    },
                )
        except Exception as e:
            raise ValidationError(
                _('Could not validate file type: %(error)s'),
                params={'error': str(e)},
            )


class SecureFileValidator:
    """Comprehensive file security validator."""

    # Known malicious file signatures (magic bytes)
    MALICIOUS_SIGNATURES = {
        b'MZ': 'Windows executable',
        b'\x7fELF': 'Linux executable',
        b'#!/': 'Shell script',
        b'<?php': 'PHP script',
        b'<%': 'ASP script',
    }

    # Dangerous file extensions
    DANGEROUS_EXTENSIONS = [
        'exe', 'dll', 'scr', 'bat', 'cmd', 'com', 'pif',
        'sh', 'bash', 'zsh', 'fish',
        'app', 'deb', 'rpm', 'dmg', 'pkg', 'msi',
        'jar', 'jnlp', 'class',
        'py', 'pyc', 'pyo', 'pyw',
        'js', 'jse', 'vbs', 'vbe', 'wsf', 'wsh',
        'ps1', 'ps2', 'psc1', 'psc2',
        'rb', 'pl', 'php', 'asp', 'aspx', 'jsp',
    ]

    def __init__(self,
                 max_size: int = 10 * 1024 * 1024,  # 10MB default
                 allowed_extensions: Optional[List[str]] = None,
                 allowed_mimes: Optional[List[str]] = None,
                 check_content: bool = True):
        """
        Initialize comprehensive file validator.

        Args:
            max_size: Maximum file size in bytes
            allowed_extensions: Whitelist of allowed file extensions
            allowed_mimes: Whitelist of allowed MIME types
            check_content: Whether to check file content for malicious signatures
        """
        self.max_size = max_size
        self.allowed_extensions = allowed_extensions
        self.allowed_mimes = allowed_mimes
        self.check_content = check_content

    def __call__(self, value: Any) -> None:
        """Perform comprehensive file validation."""
        # Check file size
        if value.size > self.max_size:
            raise ValidationError(
                _('File size cannot exceed %(max_size)s MB.'),
                params={'max_size': self.max_size / (1024 * 1024)},
            )

        # Check file extension
        ext = os.path.splitext(value.name)[1].lower().strip('.')

        # Block dangerous extensions
        if ext in self.DANGEROUS_EXTENSIONS:
            raise ValidationError(
                _('File type "%(ext)s" is potentially dangerous and not allowed.'),
                params={'ext': ext},
            )

        # Check against whitelist if provided
        if self.allowed_extensions and ext not in self.allowed_extensions:
            raise ValidationError(
                _('File extension "%(ext)s" is not allowed. Allowed: %(allowed)s'),
                params={
                    'ext': ext,
                    'allowed': ', '.join(self.allowed_extensions)
                },
            )

        # Check MIME type if specified
        if self.allowed_mimes:
            try:
                file_content = value.read(2048)
                value.seek(0)
                mime = magic.from_buffer(file_content, mime=True)

                if mime not in self.allowed_mimes:
                    raise ValidationError(
                        _('MIME type "%(mime)s" is not allowed.'),
                        params={'mime': mime},
                    )
            except Exception as e:
                raise ValidationError(
                    _('Could not validate file type: %(error)s'),
                    params={'error': str(e)},
                )

        # Check for malicious content
        if self.check_content:
            value.seek(0)
            header = value.read(256)
            value.seek(0)

            for signature, description in self.MALICIOUS_SIGNATURES.items():
                if header.startswith(signature):
                    raise ValidationError(
                        _('File appears to be %(type)s which is not allowed.'),
                        params={'type': description},
                    )


class ImageFileValidator(SecureFileValidator):
    """Specialized validator for image files."""

    def __init__(self,
                 max_size: int = 5 * 1024 * 1024,  # 5MB default for images
                 max_width: Optional[int] = None,
                 max_height: Optional[int] = None):
        """
        Initialize image validator.

        Args:
            max_size: Maximum file size in bytes
            max_width: Maximum image width in pixels
            max_height: Maximum image height in pixels
        """
        super().__init__(
            max_size=max_size,
            allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'],
            allowed_mimes=[
                'image/jpeg', 'image/png', 'image/gif',
                'image/webp', 'image/svg+xml'
            ],
            check_content=True
        )
        self.max_width = max_width
        self.max_height = max_height

    def __call__(self, value: Any) -> None:
        """Validate image file."""
        super().__call__(value)

        # Additional image-specific validation
        if self.max_width or self.max_height:
            try:
                from PIL import Image
                value.seek(0)
                img = Image.open(value)
                width, height = img.size
                value.seek(0)

                if self.max_width and width > self.max_width:
                    raise ValidationError(
                        _('Image width cannot exceed %(max)s pixels.'),
                        params={'max': self.max_width},
                    )

                if self.max_height and height > self.max_height:
                    raise ValidationError(
                        _('Image height cannot exceed %(max)s pixels.'),
                        params={'max': self.max_height},
                    )
            except ImportError:
                pass  # PIL not installed, skip dimension check
            except Exception as e:
                raise ValidationError(
                    _('Could not validate image dimensions: %(error)s'),
                    params={'error': str(e)},
                )


class PDFFileValidator(SecureFileValidator):
    """Specialized validator for PDF files."""

    def __init__(self, max_size: int = 10 * 1024 * 1024):  # 10MB default
        """Initialize PDF validator."""
        super().__init__(
            max_size=max_size,
            allowed_extensions=['pdf'],
            allowed_mimes=['application/pdf'],
            check_content=True
        )

    def __call__(self, value: Any) -> None:
        """Validate PDF file."""
        super().__call__(value)

        # Check PDF header
        value.seek(0)
        header = value.read(5)
        value.seek(0)

        if not header.startswith(b'%PDF-'):
            raise ValidationError(_('File is not a valid PDF document.'))


class FileHashValidator:
    """Validates file integrity using cryptographic hash."""

    def __init__(self, expected_hash: Optional[str] = None, algorithm: str = 'sha256'):
        """
        Initialize hash validator.

        Args:
            expected_hash: Expected hash value (if known)
            algorithm: Hash algorithm to use
        """
        self.expected_hash = expected_hash
        self.algorithm = algorithm

    def __call__(self, value: Any) -> str:
        """
        Validate and return file hash.

        Returns:
            Calculated hash of the file
        """
        hasher = hashlib.new(self.algorithm)

        value.seek(0)
        for chunk in iter(lambda: value.read(4096), b''):
            hasher.update(chunk)
        value.seek(0)

        calculated_hash = hasher.hexdigest()

        if self.expected_hash and calculated_hash != self.expected_hash:
            raise ValidationError(
                _('File integrity check failed. The file may be corrupted or tampered with.')
            )

        return calculated_hash


class AntiVirusValidator:
    """Placeholder for anti-virus scanning integration."""

    def __init__(self, scanner: Optional[Any] = None):
        """
        Initialize anti-virus validator.

        Args:
            scanner: Anti-virus scanner instance (e.g., ClamAV)
        """
        self.scanner = scanner

    def __call__(self, value: Any) -> None:
        """Scan file for viruses."""
        if not self.scanner:
            # Skip if no scanner configured
            return

        # This is a placeholder - implement actual AV scanning
        # Example with ClamAV:
        # result = self.scanner.scan_stream(value)
        # if result and result.get('infected'):
        #     raise ValidationError(_('File contains malware: %(threat)s'),
        #                         params={'threat': result.get('threat_name')})
        pass


# Convenience validators
validate_image = ImageFileValidator()
validate_pdf = PDFFileValidator()
validate_document = SecureFileValidator(
    allowed_extensions=['pdf', 'doc', 'docx', 'odt', 'txt', 'rtf'],
    allowed_mimes=[
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.oasis.opendocument.text',
        'text/plain',
        'text/rtf',
    ]
)