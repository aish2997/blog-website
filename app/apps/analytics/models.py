from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.db.models import Count, Sum
from datetime import datetime, timedelta


class Visitor(models.Model):
    """Track unique visitors to the site"""
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()

    # Session tracking
    session_key = models.CharField(max_length=255, unique=True)

    # Visitor details
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    operating_system = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=50, blank=True)  # mobile, tablet, desktop

    # Referrer info
    referrer_url = models.URLField(blank=True, null=True)
    referrer_domain = models.CharField(max_length=255, blank=True)

    # Landing page
    landing_page = models.CharField(max_length=500)

    # Timestamps
    first_visit = models.DateTimeField(auto_now_add=True)
    last_visit = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_visit']
        indexes = [
            models.Index(fields=['session_key']),
            models.Index(fields=['-first_visit']),
        ]

    def __str__(self):
        return f"Visitor from {self.ip_address} - {self.first_visit}"


class PageView(models.Model):
    """Track page views for analytics"""
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name='page_views')

    # Page details
    path = models.CharField(max_length=500)
    title = models.CharField(max_length=200, blank=True)

    # Optional: Link to specific content
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Time tracking
    timestamp = models.DateTimeField(auto_now_add=True)
    time_on_page = models.PositiveIntegerField(default=0, help_text="Time spent on page in seconds")

    # Page metrics
    is_bounce = models.BooleanField(default=False)
    exit_page = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['path', '-timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.path} - {self.timestamp}"


class SiteStatistics(models.Model):
    """Aggregate site statistics - computed daily"""
    date = models.DateField(unique=True)

    # Visitor metrics
    unique_visitors = models.PositiveIntegerField(default=0)
    total_page_views = models.PositiveIntegerField(default=0)
    bounce_rate = models.FloatField(default=0.0)
    avg_session_duration = models.FloatField(default=0.0, help_text="Average session duration in seconds")

    # Content metrics
    blog_views = models.PositiveIntegerField(default=0)
    project_views = models.PositiveIntegerField(default=0)
    cv_views = models.PositiveIntegerField(default=0)
    cv_downloads = models.PositiveIntegerField(default=0)

    # Engagement metrics
    comments_submitted = models.PositiveIntegerField(default=0)
    comments_approved = models.PositiveIntegerField(default=0)

    # Top content (stored as JSON)
    top_blog_posts = models.JSONField(default=list, blank=True)
    top_projects = models.JSONField(default=list, blank=True)
    top_referrers = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Site Statistics'

    def __str__(self):
        return f"Stats for {self.date}"

    @classmethod
    def calculate_daily_stats(cls, date=None):
        """Calculate and store daily statistics"""
        if date is None:
            date = timezone.now().date()

        # Get or create stats for the date
        stats, created = cls.objects.get_or_create(date=date)

        # Calculate metrics for the day
        start_time = datetime.combine(date, datetime.min.time())
        end_time = datetime.combine(date, datetime.max.time())

        # Unique visitors
        stats.unique_visitors = Visitor.objects.filter(
            first_visit__range=(start_time, end_time)
        ).count()

        # Page views
        stats.total_page_views = PageView.objects.filter(
            timestamp__range=(start_time, end_time)
        ).count()

        stats.save()
        return stats


class EventTracking(models.Model):
    """Track custom events (downloads, external link clicks, etc.)"""
    EVENT_TYPES = (
        ('download', 'File Download'),
        ('external_link', 'External Link Click'),
        ('social_share', 'Social Share'),
        ('contact_form', 'Contact Form Submission'),
        ('search', 'Search Query'),
        ('cv_download', 'CV Download'),
        ('github_click', 'GitHub Link Click'),
        ('demo_click', 'Demo Link Click'),
    )

    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name='events', null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    event_category = models.CharField(max_length=100)
    event_action = models.CharField(max_length=100)
    event_label = models.CharField(max_length=200, blank=True)
    event_value = models.CharField(max_length=200, blank=True)

    # Additional context
    page_url = models.CharField(max_length=500)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.event_type}: {self.event_action} - {self.timestamp}"


class SearchQuery(models.Model):
    """Track search queries for insights"""
    query = models.CharField(max_length=255)
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name='searches', null=True, blank=True)
    results_count = models.PositiveIntegerField(default=0)
    clicked_result = models.BooleanField(default=False)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Search Queries'

    def __str__(self):
        return f"Search: {self.query}"
