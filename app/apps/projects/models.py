from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from taggit.managers import TaggableManager
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify


class ProjectCategory(models.Model):
    """Project categories"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Project Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class TechnologyStack(models.Model):
    """Technologies used in projects"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=100, blank=True, help_text="Icon URL or class")
    website = models.URLField(blank=True)
    color = models.CharField(max_length=7, blank=True, help_text="Hex color code")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Technology Stack'
        verbose_name_plural = 'Technology Stacks'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Project(models.Model):
    """Portfolio projects with GitHub integration"""
    STATUS_CHOICES = (
        ('planning', 'Planning'),
        ('development', 'In Development'),
        ('completed', 'Completed'),
        ('maintained', 'Actively Maintained'),
        ('archived', 'Archived'),
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.ForeignKey(ProjectCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')

    # Description
    short_description = models.TextField(max_length=500)
    description = MarkdownxField(help_text="Detailed project description in Markdown")

    # Links
    github_url = models.URLField(blank=True, help_text="GitHub repository URL")
    live_url = models.URLField(blank=True, help_text="Live demo URL")
    documentation_url = models.URLField(blank=True, help_text="Documentation URL")

    # Technologies
    technologies = models.ManyToManyField(TechnologyStack, blank=True, related_name='projects')
    tags = TaggableManager(blank=True)

    # Relations
    comments = GenericRelation('comments.Comment', related_query_name='project')

    # Media
    featured_image = models.ImageField(upload_to='projects/featured/', blank=True, null=True)
    gallery_images = models.JSONField(default=list, blank=True, help_text="List of image URLs for project gallery")

    # Meta
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='development')
    featured = models.BooleanField(default=False, help_text="Featured projects appear on homepage")
    is_public = models.BooleanField(default=True)

    # GitHub Stats (can be updated via API)
    github_stars = models.PositiveIntegerField(default=0)
    github_forks = models.PositiveIntegerField(default=0)
    github_watchers = models.PositiveIntegerField(default=0)
    last_github_update = models.DateTimeField(blank=True, null=True)

    # Analytics
    view_count = models.PositiveIntegerField(default=0)

    # Dates
    start_date = models.DateField(blank=True, null=True)
    completion_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-featured', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('projects:project_detail', kwargs={'slug': self.slug})

    def get_markdown_description(self):
        """Return HTML rendered markdown description"""
        return markdownify(self.description)

    def increment_view_count(self):
        """Increment view counter"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    @property
    def duration(self):
        """Calculate project duration"""
        if self.start_date and self.completion_date:
            delta = self.completion_date - self.start_date
            months = delta.days // 30
            if months > 0:
                return f"{months} month{'s' if months > 1 else ''}"
            else:
                return f"{delta.days} day{'s' if delta.days > 1 else ''}"
        return None

    @property
    def comments_count(self):
        return self.comments.filter(is_approved=True).count()

    def update_github_stats(self):
        """Update GitHub statistics from API"""
        # This would be implemented to fetch data from GitHub API
        # For now, it's a placeholder
        pass
