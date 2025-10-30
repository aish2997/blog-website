"""
Signals for the comments app.

This module handles automatic cleanup of comments when their parent objects
(BlogPost or Project) are deleted. Since GenericForeignKey doesn't support
CASCADE on delete, we need to manually handle this cleanup.
"""

import logging
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)


@receiver(pre_delete, sender='blog.BlogPost')
def delete_blogpost_comments(sender, instance, **kwargs):
    """
    Delete all comments associated with a BlogPost before the BlogPost is deleted.

    This prevents orphaned comments from remaining in the database when a
    BlogPost is deleted.
    """
    from apps.comments.models import Comment

    # Get the ContentType for BlogPost
    content_type = ContentType.objects.get_for_model(instance)

    # Find all comments for this BlogPost
    comments = Comment.objects.filter(
        content_type=content_type,
        object_id=instance.pk
    )

    comment_count = comments.count()

    if comment_count > 0:
        logger.info(
            f"Deleting {comment_count} comment(s) associated with "
            f"BlogPost '{instance.title}' (ID: {instance.pk})"
        )
        comments.delete()


@receiver(pre_delete, sender='projects.Project')
def delete_project_comments(sender, instance, **kwargs):
    """
    Delete all comments associated with a Project before the Project is deleted.

    This prevents orphaned comments from remaining in the database when a
    Project is deleted.
    """
    from apps.comments.models import Comment

    # Get the ContentType for Project
    content_type = ContentType.objects.get_for_model(instance)

    # Find all comments for this Project
    comments = Comment.objects.filter(
        content_type=content_type,
        object_id=instance.pk
    )

    comment_count = comments.count()

    if comment_count > 0:
        logger.info(
            f"Deleting {comment_count} comment(s) associated with "
            f"Project '{instance.title}' (ID: {instance.pk})"
        )
        comments.delete()
