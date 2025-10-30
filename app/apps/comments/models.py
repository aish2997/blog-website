from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.core.validators import EmailValidator
import hashlib


class Comment(models.Model):
    """Authenticated comments with Google Sign-In for blog posts and projects"""
    # Generic relation to allow comments on both Blog and Project models
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # User (required - must be signed in with Google to comment)
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="User who posted this comment (authenticated via Google)"
    )

    # User profile info from Google
    profile_picture_url = models.URLField(
        blank=True,
        max_length=500,
        help_text="Google profile picture URL"
    )

    # Comment data
    content = models.TextField(max_length=1000)

    # Parent comment for replies
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )

    # Edit tracking
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(blank=True, null=True)

    # Moderation (authenticated users auto-approved)
    is_approved = models.BooleanField(
        default=True,
        help_text="Authenticated users are auto-approved"
    )
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
        """String representation showing user and content object"""
        user_display = self.user.get_full_name() or self.user.email or self.user.username
        return f"Comment by {user_display} on {self.content_object}"

    def save(self, *args, **kwargs):
        """Custom save to handle timestamps and profile picture"""
        # Set approved timestamp when comment is approved
        if self.is_approved and not self.approved_at:
            self.approved_at = timezone.now()

        # Set edited timestamp when content is modified (not on initial creation)
        if self.pk and self.is_edited:
            self.edited_at = timezone.now()

        # Fetch Google profile picture URL if not set
        if not self.profile_picture_url and hasattr(self.user, 'socialaccount_set'):
            # Get Google social account
            google_account = self.user.socialaccount_set.filter(provider='google').first()
            if google_account and google_account.extra_data:
                self.profile_picture_url = google_account.extra_data.get('picture', '')

        super().save(*args, **kwargs)

    def get_avatar_url(self):
        """Get user's Google profile picture or fallback to Gravatar"""
        # Use Google profile picture if available
        if self.profile_picture_url:
            return self.profile_picture_url

        # Fallback to Gravatar based on user's email
        if self.user.email:
            email_hash = hashlib.md5(self.user.email.lower().encode()).hexdigest()
            return f"https://www.gravatar.com/avatar/{email_hash}?d=identicon&s=80"

        # Final fallback
        return f"https://www.gravatar.com/avatar/default?d=identicon&s=80"

    def get_author_name(self):
        """Get display name for the comment author"""
        return self.user.get_full_name() or self.user.email.split('@')[0] if self.user.email else self.user.username

    def can_edit(self, user):
        """Check if user can edit this comment"""
        return user.is_authenticated and user == self.user

    def can_delete(self, user):
        """Check if user can delete this comment"""
        return user.is_authenticated and (user == self.user or user.is_staff)

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
