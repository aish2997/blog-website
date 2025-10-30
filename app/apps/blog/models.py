from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from taggit.managers import TaggableManager
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify


class Category(models.Model):
    """Blog post categories"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:category', kwargs={'slug': self.slug})


class BlogPost(models.Model):
    """Blog post model with markdown support"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')

    # Content
    content = MarkdownxField(help_text="Use Markdown formatting")
    excerpt = models.TextField(max_length=500, help_text="Short description for previews")
    featured_image = models.ImageField(upload_to='blog/featured/', blank=True, null=True)

    # Meta
    tags = TaggableManager(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False, help_text="Featured posts appear on homepage")

    # Relations
    comments = GenericRelation('comments.Comment', related_query_name='blogpost')

    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=250, blank=True)

    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    read_time = models.PositiveIntegerField(default=0, help_text="Estimated read time in minutes")

    # Timestamps
    published_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_date', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status', '-published_date']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Auto-calculate read time based on word count
        if self.content:
            word_count = len(self.content.split())
            self.read_time = max(1, word_count // 200)  # Assuming 200 words per minute

        # Set published date when status changes to published
        if self.status == 'published' and not self.published_date:
            self.published_date = timezone.now()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    def get_markdown_content(self):
        """Return HTML rendered markdown content"""
        return markdownify(self.content)

    def increment_view_count(self):
        """Increment view counter"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    @property
    def is_published(self):
        return self.status == 'published'

    @property
    def comments_count(self):
        return self.comments.filter(is_approved=True).count()

    @property
    def related_posts(self):
        """Get related posts based on tags and category"""
        # Start with posts that share tags
        if self.tags.exists():
            related = BlogPost.objects.filter(
                status='published',
                tags__in=self.tags.all()
            ).exclude(id=self.id).distinct()[:3]

            # If we don't have enough, add posts from same category
            if related.count() < 3 and self.category:
                needed = 3 - related.count()
                category_posts = BlogPost.objects.filter(
                    status='published',
                    category=self.category
                ).exclude(id=self.id).exclude(
                    id__in=related.values_list('id', flat=True)
                )[:needed]

                # Combine the querysets
                related = list(related) + list(category_posts)
                return related[:3]

            return related

        # If no tags, just get posts from same category
        elif self.category:
            return BlogPost.objects.filter(
                status='published',
                category=self.category
            ).exclude(id=self.id)[:3]

        # If no tags or category, just get recent posts
        return BlogPost.objects.filter(
            status='published'
        ).exclude(id=self.id)[:3]
