"""
Management command to verify Django admin panel static files and configuration.

This command performs comprehensive checks to ensure the admin panel will render
correctly in both development and production environments.
"""

import os
import sys
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.admin.sites import site
from django.test.client import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from pathlib import Path


class Command(BaseCommand):
    help = 'Verifies Django admin panel configuration and static files'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.errors = []
        self.warnings = []
        self.successes = []

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed verification output',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix common issues automatically',
        )

    def handle(self, *args, **options):
        self.verbose = options.get('verbose', False)
        self.fix = options.get('fix', False)

        self.stdout.write(self.style.NOTICE('=' * 70))
        self.stdout.write(self.style.NOTICE('Django Admin Panel Verification'))
        self.stdout.write(self.style.NOTICE('=' * 70))

        # Run all verification checks
        self.check_admin_enabled()
        self.check_admin_url_configured()
        self.check_static_files_configuration()
        self.check_admin_static_files()
        self.check_middleware_configuration()
        self.check_security_headers()
        self.check_admin_templates()
        self.check_admin_access()

        # Display results
        self.display_results()

        # Return appropriate exit code
        if self.errors:
            sys.exit(1)
        sys.exit(0)

    def check_admin_enabled(self):
        """Check if Django admin is properly enabled in INSTALLED_APPS."""
        self.stdout.write('\n' + self.style.HTTP_INFO('Checking admin configuration...'))

        if 'django.contrib.admin' not in settings.INSTALLED_APPS:
            self.errors.append('django.contrib.admin is not in INSTALLED_APPS')
            return

        if 'django.contrib.contenttypes' not in settings.INSTALLED_APPS:
            self.errors.append('django.contrib.contenttypes is not in INSTALLED_APPS (required for admin)')
            return

        if 'django.contrib.auth' not in settings.INSTALLED_APPS:
            self.errors.append('django.contrib.auth is not in INSTALLED_APPS (required for admin)')
            return

        if 'django.contrib.messages' not in settings.INSTALLED_APPS:
            self.errors.append('django.contrib.messages is not in INSTALLED_APPS (required for admin)')
            return

        if 'django.contrib.sessions' not in settings.INSTALLED_APPS:
            self.errors.append('django.contrib.sessions is not in INSTALLED_APPS (required for admin)')
            return

        self.successes.append('Admin apps properly configured in INSTALLED_APPS')

    def check_admin_url_configured(self):
        """Check if admin URLs are properly configured."""
        self.stdout.write('\n' + self.style.HTTP_INFO('Checking admin URL configuration...'))

        try:
            admin_url = reverse('admin:index')
            self.successes.append(f'Admin URL configured at: {admin_url}')
        except Exception as e:
            self.errors.append(f'Admin URL not properly configured: {e}')

    def check_static_files_configuration(self):
        """Check static files configuration."""
        self.stdout.write('\n' + self.style.HTTP_INFO('Checking static files configuration...'))

        # Check STATIC_URL
        if not hasattr(settings, 'STATIC_URL'):
            self.errors.append('STATIC_URL is not configured')
        else:
            self.successes.append(f'STATIC_URL: {settings.STATIC_URL}')

        # Check STATIC_ROOT
        if not hasattr(settings, 'STATIC_ROOT'):
            self.warnings.append('STATIC_ROOT is not configured')
        else:
            self.successes.append(f'STATIC_ROOT: {settings.STATIC_ROOT}')

        # Check STATICFILES_DIRS
        if hasattr(settings, 'STATICFILES_DIRS'):
            for static_dir in settings.STATICFILES_DIRS:
                if os.path.exists(static_dir):
                    self.successes.append(f'Static directory exists: {static_dir}')
                else:
                    self.warnings.append(f'Static directory does not exist: {static_dir}')

        # Check staticfiles app
        if 'django.contrib.staticfiles' not in settings.INSTALLED_APPS:
            self.errors.append('django.contrib.staticfiles is not in INSTALLED_APPS')
        else:
            self.successes.append('Staticfiles app is installed')

    def check_admin_static_files(self):
        """Check if admin static files are accessible."""
        self.stdout.write('\n' + self.style.HTTP_INFO('Checking admin static files...'))

        # Key admin static files to check
        admin_files = [
            'admin/css/base.css',
            'admin/css/dashboard.css',
            'admin/css/forms.css',
            'admin/js/admin/RelatedObjectLookups.js',
            'admin/js/core.js',
        ]

        # Check in STATIC_ROOT if it exists and is populated
        if hasattr(settings, 'STATIC_ROOT') and os.path.exists(settings.STATIC_ROOT):
            for file_path in admin_files:
                full_path = os.path.join(settings.STATIC_ROOT, file_path)
                if os.path.exists(full_path):
                    if self.verbose:
                        self.successes.append(f'Found: {file_path}')
                else:
                    self.warnings.append(f'Missing in STATIC_ROOT: {file_path}')

        # Check if collectstatic has been run
        if hasattr(settings, 'STATIC_ROOT'):
            admin_css_dir = os.path.join(settings.STATIC_ROOT, 'admin', 'css')
            if not os.path.exists(admin_css_dir):
                self.warnings.append('Admin static files not collected. Run: python manage.py collectstatic')
                if self.fix:
                    self.stdout.write(self.style.WARNING('Attempting to run collectstatic...'))
                    os.system('python manage.py collectstatic --noinput')

        # Success message if no issues
        if not any(f'Missing in STATIC_ROOT' in w for w in self.warnings):
            self.successes.append('Admin static files are present')

    def check_middleware_configuration(self):
        """Check middleware configuration for admin."""
        self.stdout.write('\n' + self.style.HTTP_INFO('Checking middleware configuration...'))

        required_middleware = [
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ]

        for mw in required_middleware:
            if mw not in settings.MIDDLEWARE:
                self.errors.append(f'Required middleware missing: {mw}')

        # Check for custom admin middleware
        if 'portfolio.middleware.AdminSecurityMiddleware' in settings.MIDDLEWARE:
            self.successes.append('Custom AdminSecurityMiddleware is configured')
        else:
            self.warnings.append('Custom AdminSecurityMiddleware not found (admin may have security issues)')

        # Check WhiteNoise configuration
        if 'whitenoise.middleware.WhiteNoiseMiddleware' in settings.MIDDLEWARE:
            self.successes.append('WhiteNoise middleware is configured')

            # Check if it's in the correct position (after SecurityMiddleware)
            mw_list = list(settings.MIDDLEWARE)
            sec_idx = mw_list.index('django.middleware.security.SecurityMiddleware')
            wn_idx = mw_list.index('whitenoise.middleware.WhiteNoiseMiddleware')
            if wn_idx == sec_idx + 1:
                self.successes.append('WhiteNoise is correctly positioned after SecurityMiddleware')
            else:
                self.warnings.append('WhiteNoise should be directly after SecurityMiddleware')

    def check_security_headers(self):
        """Check security header configuration."""
        self.stdout.write('\n' + self.style.HTTP_INFO('Checking security headers...'))

        # Check X-Frame-Options
        x_frame = getattr(settings, 'X_FRAME_OPTIONS', None)
        if x_frame == 'DENY':
            self.errors.append('X_FRAME_OPTIONS is set to DENY - this will break admin panel')
            if self.fix:
                self.stdout.write(self.style.WARNING('X_FRAME_OPTIONS should be SAMEORIGIN for admin to work'))
        elif x_frame == 'SAMEORIGIN':
            self.successes.append('X_FRAME_OPTIONS correctly set to SAMEORIGIN')
        else:
            self.warnings.append(f'X_FRAME_OPTIONS is set to: {x_frame}')

        # Check other security settings
        if settings.DEBUG:
            self.successes.append('DEBUG mode - security headers relaxed')
        else:
            security_settings = [
                ('SECURE_SSL_REDIRECT', 'SSL redirect'),
                ('SESSION_COOKIE_SECURE', 'Secure session cookies'),
                ('CSRF_COOKIE_SECURE', 'Secure CSRF cookies'),
                ('SECURE_BROWSER_XSS_FILTER', 'XSS filter'),
                ('SECURE_CONTENT_TYPE_NOSNIFF', 'Content type nosniff'),
            ]

            for setting_name, description in security_settings:
                if getattr(settings, setting_name, False):
                    if self.verbose:
                        self.successes.append(f'{description} is enabled')

    def check_admin_templates(self):
        """Check for custom admin templates that might override defaults."""
        self.stdout.write('\n' + self.style.HTTP_INFO('Checking admin templates...'))

        template_dirs = []
        for template_config in settings.TEMPLATES:
            template_dirs.extend(template_config.get('DIRS', []))

        custom_admin_found = False
        for template_dir in template_dirs:
            admin_dir = Path(template_dir) / 'admin'
            if admin_dir.exists():
                custom_admin_found = True
                self.warnings.append(f'Custom admin templates found at: {admin_dir}')
                if self.verbose:
                    for template in admin_dir.glob('*.html'):
                        self.stdout.write(f'  - {template.name}')

        if not custom_admin_found:
            self.successes.append('No custom admin templates (using Django defaults)')

    def check_admin_access(self):
        """Test actual admin access with a test client."""
        self.stdout.write('\n' + self.style.HTTP_INFO('Testing admin access...'))

        client = Client()

        # Test admin login page
        try:
            response = client.get('/admin/login/')
            if response.status_code == 200:
                self.successes.append('Admin login page is accessible')

                # Check if CSS is loaded (basic check)
                if b'admin/css/base.css' in response.content:
                    self.successes.append('Admin CSS references found in HTML')
                else:
                    self.warnings.append('Admin CSS references not found in HTML')
            else:
                self.errors.append(f'Admin login page returned status: {response.status_code}')
        except Exception as e:
            self.errors.append(f'Could not access admin login: {e}')

    def display_results(self):
        """Display verification results."""
        self.stdout.write('\n' + self.style.NOTICE('=' * 70))
        self.stdout.write(self.style.NOTICE('Verification Results'))
        self.stdout.write(self.style.NOTICE('=' * 70))

        # Display successes
        if self.successes:
            self.stdout.write('\n' + self.style.SUCCESS(f'✓ Passed ({len(self.successes)} checks)'))
            if self.verbose:
                for success in self.successes:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {success}'))

        # Display warnings
        if self.warnings:
            self.stdout.write('\n' + self.style.WARNING(f'⚠ Warnings ({len(self.warnings)} items)'))
            for warning in self.warnings:
                self.stdout.write(self.style.WARNING(f'  ⚠ {warning}'))

        # Display errors
        if self.errors:
            self.stdout.write('\n' + self.style.ERROR(f'✗ Errors ({len(self.errors)} items)'))
            for error in self.errors:
                self.stdout.write(self.style.ERROR(f'  ✗ {error}'))

        # Summary
        self.stdout.write('\n' + self.style.NOTICE('=' * 70))
        if self.errors:
            self.stdout.write(self.style.ERROR('Admin panel verification FAILED'))
            self.stdout.write(self.style.ERROR('Please fix the errors above before using admin'))
        elif self.warnings:
            self.stdout.write(self.style.WARNING('Admin panel verification PASSED with warnings'))
            self.stdout.write(self.style.WARNING('Admin should work but consider fixing warnings'))
        else:
            self.stdout.write(self.style.SUCCESS('Admin panel verification PASSED'))
            self.stdout.write(self.style.SUCCESS('Admin panel is properly configured'))

        # Provide next steps
        if self.errors or self.warnings:
            self.stdout.write('\n' + self.style.NOTICE('Next steps:'))
            if any('collectstatic' in w for w in self.warnings):
                self.stdout.write('  1. Run: python manage.py collectstatic')
            if any('X_FRAME_OPTIONS' in e for e in self.errors):
                self.stdout.write('  2. Change X_FRAME_OPTIONS from DENY to SAMEORIGIN in settings')
            if any('AdminSecurityMiddleware' in w for w in self.warnings):
                self.stdout.write('  3. Ensure portfolio.middleware.AdminSecurityMiddleware is in MIDDLEWARE')