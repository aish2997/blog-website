from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Comment, CommentFlag


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author_name', 'content_short', 'content_object_link', 'is_approved',
                    'is_featured', 'is_spam', 'created_at']
    list_filter = ['is_approved', 'is_featured', 'is_spam', 'created_at', 'content_type']
    search_fields = ['author_name', 'author_email', 'content', 'ip_address']
    list_editable = ['is_approved', 'is_featured', 'is_spam']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['content_type', 'object_id', 'content_object', 'ip_address',
                       'user_agent', 'created_at', 'updated_at', 'approved_at', 'approved_by']

    fieldsets = (
        ('Comment Content', {
            'fields': ('author_name', 'author_email', 'content', 'parent')
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id', 'content_object'),
        }),
        ('Moderation', {
            'fields': ('is_approved', 'is_featured', 'is_spam', 'approved_at', 'approved_by')
        }),
        ('Tracking', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def content_short(self, obj):
        """Display truncated content"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_short.short_description = 'Comment'

    def content_object_link(self, obj):
        """Link to the commented object"""
        if obj.content_object:
            app_label = obj.content_type.app_label
            model_name = obj.content_type.model

            # Try to generate admin URL for the object
            try:
                url = reverse(f'admin:{app_label}_{model_name}_change', args=[obj.object_id])
                return format_html('<a href="{}">{}</a>', url, str(obj.content_object))
            except:
                return str(obj.content_object)
        return '-'
    content_object_link.short_description = 'Commented On'

    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related(
            'content_type', 'parent', 'approved_by'
        )

    def save_model(self, request, obj, form, change):
        """Set approved_by when approving comment"""
        if obj.is_approved and not obj.approved_by:
            obj.approved_by = request.user
            obj.approved_at = timezone.now()
        super().save_model(request, obj, form, change)

    actions = ['approve_comments', 'reject_comments', 'mark_as_spam',
               'mark_as_not_spam', 'feature_comments', 'unfeature_comments']

    def approve_comments(self, request, queryset):
        count = 0
        for comment in queryset:
            if not comment.is_approved:
                comment.is_approved = True
                comment.approved_by = request.user
                comment.approved_at = timezone.now()
                comment.is_spam = False
                comment.save()
                count += 1
        self.message_user(request, f"{count} comments have been approved.")
    approve_comments.short_description = "Approve selected comments"

    def reject_comments(self, request, queryset):
        updated = queryset.update(is_approved=False, is_featured=False)
        self.message_user(request, f"{updated} comments have been rejected.")
    reject_comments.short_description = "Reject selected comments"

    def mark_as_spam(self, request, queryset):
        updated = queryset.update(is_spam=True, is_approved=False, is_featured=False)
        self.message_user(request, f"{updated} comments marked as spam.")
    mark_as_spam.short_description = "Mark as spam"

    def mark_as_not_spam(self, request, queryset):
        updated = queryset.update(is_spam=False)
        self.message_user(request, f"{updated} comments marked as not spam.")
    mark_as_not_spam.short_description = "Mark as not spam"

    def feature_comments(self, request, queryset):
        # Only feature approved comments
        updated = queryset.filter(is_approved=True).update(is_featured=True)
        self.message_user(request, f"{updated} comments have been featured.")
    feature_comments.short_description = "Feature selected comments"

    def unfeature_comments(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f"{updated} comments have been unfeatured.")
    unfeature_comments.short_description = "Unfeature selected comments"

    class Media:
        css = {
            'all': ('admin/css/comments_admin.css',)
        }


@admin.register(CommentFlag)
class CommentFlagAdmin(admin.ModelAdmin):
    list_display = ['comment_short', 'reason', 'resolved', 'resolved_by', 'created_at']
    list_filter = ['reason', 'resolved', 'created_at']
    search_fields = ['comment__content', 'description']
    list_editable = ['resolved']
    date_hierarchy = 'created_at'
    ordering = ['resolved', '-created_at']
    readonly_fields = ['comment', 'ip_address', 'created_at', 'resolved_at', 'resolved_by']

    fieldsets = (
        ('Flag Details', {
            'fields': ('comment', 'reason', 'description')
        }),
        ('Resolution', {
            'fields': ('resolved', 'resolved_by', 'resolved_at')
        }),
        ('Tracking', {
            'fields': ('ip_address', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def comment_short(self, obj):
        """Display truncated comment content"""
        content = obj.comment.content
        return content[:50] + '...' if len(content) > 50 else content
    comment_short.short_description = 'Comment'

    def save_model(self, request, obj, form, change):
        """Set resolved_by when resolving flag"""
        if obj.resolved and not obj.resolved_by:
            obj.resolved_by = request.user
            obj.resolved_at = timezone.now()
        super().save_model(request, obj, form, change)

    actions = ['resolve_flags', 'unresolve_flags']

    def resolve_flags(self, request, queryset):
        count = 0
        for flag in queryset:
            if not flag.resolved:
                flag.resolved = True
                flag.resolved_by = request.user
                flag.resolved_at = timezone.now()
                flag.save()
                count += 1
        self.message_user(request, f"{count} flags have been resolved.")
    resolve_flags.short_description = "Resolve selected flags"

    def unresolve_flags(self, request, queryset):
        updated = queryset.update(resolved=False, resolved_by=None, resolved_at=None)
        self.message_user(request, f"{updated} flags have been unresolved.")
    unresolve_flags.short_description = "Unresolve selected flags"
