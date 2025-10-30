from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin
from .models import Project, ProjectCategory, TechnologyStack


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'order']
    list_editable = ['order']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    ordering = ['order', 'name']


@admin.register(TechnologyStack)
class TechnologyStackAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'website', 'color']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    ordering = ['name']


@admin.register(Project)
class ProjectAdmin(MarkdownxModelAdmin):
    list_display = ['title', 'category', 'status', 'featured', 'is_public',
                    'view_count', 'github_stars', 'created_at']
    list_filter = ['status', 'featured', 'is_public', 'category', 'technologies']
    search_fields = ['title', 'description', 'short_description', 'tags__name']
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['author']
    filter_horizontal = ['technologies']
    readonly_fields = ['view_count', 'github_stars', 'github_forks',
                       'github_watchers', 'last_github_update', 'created_at', 'updated_at']
    list_editable = ['status', 'featured', 'is_public']
    date_hierarchy = 'created_at'
    ordering = ['-featured', '-created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('author', 'title', 'slug', 'category')
        }),
        ('Description', {
            'fields': ('short_description', 'description', 'featured_image', 'gallery_images')
        }),
        ('Links', {
            'fields': ('github_url', 'live_url', 'documentation_url')
        }),
        ('Technologies & Tags', {
            'fields': ('technologies', 'tags')
        }),
        ('Status & Visibility', {
            'fields': ('status', 'featured', 'is_public')
        }),
        ('Timeline', {
            'fields': ('start_date', 'completion_date'),
            'classes': ('collapse',)
        }),
        ('GitHub Stats', {
            'fields': ('github_stars', 'github_forks', 'github_watchers', 'last_github_update'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('view_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        return super().get_queryset(request).select_related(
            'author', 'category'
        ).prefetch_related('technologies', 'tags')

    def save_model(self, request, obj, form, change):
        """Auto-set author on first save"""
        if not change and not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    actions = ['make_featured', 'remove_featured', 'make_public', 'make_private',
               'update_github_stats']

    def make_featured(self, request, queryset):
        updated = queryset.update(featured=True)
        self.message_user(request, f"{updated} projects have been featured.")
    make_featured.short_description = "Feature selected projects"

    def remove_featured(self, request, queryset):
        updated = queryset.update(featured=False)
        self.message_user(request, f"{updated} projects have been unfeatured.")
    remove_featured.short_description = "Unfeature selected projects"

    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f"{updated} projects have been made public.")
    make_public.short_description = "Make selected projects public"

    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f"{updated} projects have been made private.")
    make_private.short_description = "Make selected projects private"

    def update_github_stats(self, request, queryset):
        for project in queryset:
            project.update_github_stats()
        self.message_user(request, f"GitHub stats updated for {queryset.count()} projects.")
    update_github_stats.short_description = "Update GitHub statistics"
