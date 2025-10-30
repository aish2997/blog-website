"""
Management command to clean orphaned comments.

Orphaned comments are comments that reference BlogPost or Project objects
that no longer exist in the database. This typically happens when:
1. A BlogPost/Project is deleted but comments remain
2. Database backup/restore processes leave inconsistent data
3. Manual database operations delete parent objects

This command identifies and removes these orphaned comments.
"""

import logging
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from apps.comments.models import Comment

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean orphaned comments that reference deleted BlogPost or Project objects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information about each orphaned comment',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']

        self.stdout.write(self.style.NOTICE('Scanning for orphaned comments...'))

        # Get all comments
        all_comments = Comment.objects.select_related('content_type').all()
        total_comments = all_comments.count()

        orphaned_comments = []
        orphaned_by_type = {}

        # Check each comment to see if its content_object exists
        for comment in all_comments:
            try:
                # Try to access the content_object
                if comment.content_object is None:
                    orphaned_comments.append(comment)

                    # Track by content type for statistics
                    model_name = comment.content_type.model if comment.content_type else 'Unknown'
                    if model_name not in orphaned_by_type:
                        orphaned_by_type[model_name] = []
                    orphaned_by_type[model_name].append(comment)

                    if verbose:
                        self.stdout.write(
                            f"  - Comment ID {comment.id}: '{comment.content[:50]}...' "
                            f"references deleted {model_name} #{comment.object_id}"
                        )
            except Exception as e:
                # If there's an error accessing the comment, log it
                logger.error(f"Error checking comment {comment.id}: {e}")
                self.stdout.write(
                    self.style.ERROR(f"Error checking comment {comment.id}: {e}")
                )

        # Display statistics
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.NOTICE('SUMMARY'))
        self.stdout.write('=' * 60)
        self.stdout.write(f"Total comments: {total_comments}")
        self.stdout.write(f"Orphaned comments: {len(orphaned_comments)}")

        if orphaned_by_type:
            self.stdout.write('\nOrphaned comments by type:')
            for model_name, comments in orphaned_by_type.items():
                self.stdout.write(f"  - {model_name}: {len(comments)} comment(s)")

        # Delete or show what would be deleted
        if orphaned_comments:
            if dry_run:
                self.stdout.write('\n' + self.style.WARNING(
                    f"DRY RUN: Would delete {len(orphaned_comments)} orphaned comment(s)"
                ))
                self.stdout.write(
                    "Run without --dry-run to actually delete these comments"
                )
            else:
                self.stdout.write('\n' + self.style.WARNING(
                    f"Deleting {len(orphaned_comments)} orphaned comment(s)..."
                ))

                deleted_count = 0
                for comment in orphaned_comments:
                    try:
                        comment_id = comment.id
                        comment.delete()
                        deleted_count += 1
                        if verbose:
                            self.stdout.write(f"  ✓ Deleted comment {comment_id}")
                    except Exception as e:
                        logger.error(f"Error deleting comment {comment.id}: {e}")
                        self.stdout.write(
                            self.style.ERROR(f"  ✗ Failed to delete comment {comment.id}: {e}")
                        )

                self.stdout.write('\n' + self.style.SUCCESS(
                    f"Successfully deleted {deleted_count} orphaned comment(s)"
                ))
        else:
            self.stdout.write('\n' + self.style.SUCCESS(
                "No orphaned comments found. Database is clean!"
            ))

        self.stdout.write('=' * 60)
