from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin
from .models import BlogPost, Category
from apps.comments.models import Comment
from django.contrib.contenttypes.models import ContentType


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    list_editable = ['order']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    ordering = ['order', 'name']


@admin.register(BlogPost)
class BlogPostAdmin(MarkdownxModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'is_featured',
                    'view_count', 'published_date', 'created_at']
    list_filter = ['status', 'is_featured', 'category', 'published_date', 'created_at']
    search_fields = ['title', 'content', 'excerpt', 'tags__name']
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['author']
    readonly_fields = ['view_count', 'read_time', 'created_at', 'updated_at']
    list_editable = ['status', 'is_featured']
    date_hierarchy = 'published_date'
    ordering = ['-published_date', '-created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('author', 'title', 'slug', 'category')
        }),
        ('Content', {
            'fields': ('content', 'excerpt', 'featured_image')
        }),
        ('Meta Data', {
            'fields': ('tags', 'status', 'is_featured')
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('view_count', 'read_time'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('published_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        return super().get_queryset(request).select_related(
            'author', 'category'
        ).prefetch_related('tags')

    def save_model(self, request, obj, form, change):
        """Auto-set author on first save"""
        if not change and not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    # Removed custom CSS reference that was causing admin panel CSS to break
    # The file 'admin/css/blog_admin.css' didn't exist

    actions = ['publish_posts', 'unpublish_posts', 'feature_posts', 'unfeature_posts']

    def publish_posts(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f"{updated} posts have been published.")
    publish_posts.short_description = "Publish selected posts"

    def unpublish_posts(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f"{updated} posts have been unpublished.")
    unpublish_posts.short_description = "Unpublish selected posts"

    def feature_posts(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"{updated} posts have been featured.")
    feature_posts.short_description = "Feature selected posts"

    def unfeature_posts(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f"{updated} posts have been unfeatured.")
    unfeature_posts.short_description = "Unfeature selected posts"
