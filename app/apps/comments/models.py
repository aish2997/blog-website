from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.core.validators import EmailValidator
import hashlib


class Comment(models.Model):
    """Anonymous comments with moderation for blog posts and projects"""
    # Generic relation to allow comments on both Blog and Project models
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Comment data
    author_name = models.CharField(max_length=100, default="Anonymous")
    author_email = models.EmailField(
        blank=True,
        validators=[EmailValidator()],
        help_text="Email is optional and not displayed publicly"
    )
    content = models.TextField(max_length=1000)

    # Parent comment for replies
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )

    # Moderation
    is_approved = models.BooleanField(default=False, help_text="Comments require approval before display")
    is_featured = models.BooleanField(default=False, help_text="Featured comments appear at the top")
    is_spam = models.BooleanField(default=False)

    # User tracking (for rate limiting)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey(
        'auth.User',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='approved_comments'
    )

    class Meta:
        ordering = ['-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'is_approved']),
            models.Index(fields=['is_approved', '-created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.author_name} on {self.content_object}"

    def save(self, *args, **kwargs):
        # Set approved timestamp when comment is approved
        if self.is_approved and not self.approved_at:
            self.approved_at = timezone.now()
        super().save(*args, **kwargs)

    def get_avatar_url(self):
        """Generate Gravatar URL based on email"""
        if self.author_email:
            email_hash = hashlib.md5(self.author_email.lower().encode()).hexdigest()
            return f"https://www.gravatar.com/avatar/{email_hash}?d=identicon&s=50"
        # Default avatar for anonymous users
        return f"https://www.gravatar.com/avatar/{'anonymous'}?d=identicon&s=50"

    @property
    def is_reply(self):
        """Check if this comment is a reply to another comment"""
        return self.parent is not None

    @property
    def reply_count(self):
        """Count of approved replies"""
        return self.replies.filter(is_approved=True).count()


class CommentFlag(models.Model):
    """Track flagged/reported comments"""
    REASON_CHOICES = (
        ('spam', 'Spam'),
        ('offensive', 'Offensive Language'),
        ('irrelevant', 'Irrelevant/Off-topic'),
        ('other', 'Other'),
    )

    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='flags')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        'auth.User',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='resolved_flags'
    )
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Flag: {self.reason} for comment {self.comment.id}"
