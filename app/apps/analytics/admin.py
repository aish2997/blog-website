from django.contrib import admin
from django.db.models import Count, Sum, Avg
from django.utils.html import format_html
from .models import Visitor, PageView, SiteStatistics, EventTracking, SearchQuery


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'ip_address', 'country', 'city', 'browser',
                    'device_type', 'first_visit', 'last_visit']
    list_filter = ['device_type', 'browser', 'country', 'first_visit']
    search_fields = ['ip_address', 'session_key', 'country', 'city']
    readonly_fields = ['session_key', 'ip_address', 'user_agent', 'first_visit', 'last_visit']
    date_hierarchy = 'first_visit'
    ordering = ['-last_visit']

    fieldsets = (
        ('Session Info', {
            'fields': ('session_key', 'ip_address', 'user_agent')
        }),
        ('Location', {
            'fields': ('country', 'city')
        }),
        ('Device Info', {
            'fields': ('browser', 'operating_system', 'device_type')
        }),
        ('Referral', {
            'fields': ('referrer_url', 'referrer_domain', 'landing_page')
        }),
        ('Timestamps', {
            'fields': ('first_visit', 'last_visit')
        }),
    )


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ['path', 'title', 'visitor_info', 'time_on_page', 'is_bounce', 'timestamp']
    list_filter = ['is_bounce', 'exit_page', 'timestamp']
    search_fields = ['path', 'title', 'visitor__ip_address']
    readonly_fields = ['visitor', 'content_type', 'object_id', 'timestamp']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']

    def visitor_info(self, obj):
        return f"{obj.visitor.ip_address} ({obj.visitor.country})"
    visitor_info.short_description = 'Visitor'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('visitor', 'content_type')


@admin.register(SiteStatistics)
class SiteStatisticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'unique_visitors', 'total_page_views', 'bounce_rate_display',
                    'blog_views', 'project_views', 'cv_views', 'cv_downloads']
    list_filter = ['date']
    readonly_fields = ['date', 'unique_visitors', 'total_page_views', 'bounce_rate',
                       'avg_session_duration', 'blog_views', 'project_views', 'cv_views',
                       'cv_downloads', 'comments_submitted', 'comments_approved',
                       'top_blog_posts', 'top_projects', 'top_referrers',
                       'created_at', 'updated_at']
    date_hierarchy = 'date'
    ordering = ['-date']

    def bounce_rate_display(self, obj):
        return f"{obj.bounce_rate:.1f}%"
    bounce_rate_display.short_description = 'Bounce Rate'

    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('Visitor Metrics', {
            'fields': ('unique_visitors', 'total_page_views', 'bounce_rate', 'avg_session_duration')
        }),
        ('Content Metrics', {
            'fields': ('blog_views', 'project_views', 'cv_views', 'cv_downloads')
        }),
        ('Engagement', {
            'fields': ('comments_submitted', 'comments_approved')
        }),
        ('Top Content', {
            'fields': ('top_blog_posts', 'top_projects', 'top_referrers'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['recalculate_stats']

    def recalculate_stats(self, request, queryset):
        for stat in queryset:
            stat.calculate_daily_stats(stat.date)
        self.message_user(request, f"Statistics recalculated for {queryset.count()} days.")
    recalculate_stats.short_description = "Recalculate statistics for selected days"


@admin.register(EventTracking)
class EventTrackingAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'event_category', 'event_action', 'event_label',
                    'visitor_info', 'timestamp']
    list_filter = ['event_type', 'event_category', 'timestamp']
    search_fields = ['event_action', 'event_label', 'event_value', 'page_url']
    readonly_fields = ['visitor', 'ip_address', 'timestamp']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']

    def visitor_info(self, obj):
        if obj.visitor:
            return f"{obj.visitor.ip_address}"
        return obj.ip_address or '-'
    visitor_info.short_description = 'IP Address'


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ['query', 'results_count', 'clicked_result', 'visitor_info', 'timestamp']
    list_filter = ['clicked_result', 'timestamp']
    search_fields = ['query']
    readonly_fields = ['visitor', 'timestamp']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']

    def visitor_info(self, obj):
        if obj.visitor:
            return f"{obj.visitor.ip_address}"
        return '-'
    visitor_info.short_description = 'Visitor'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('visitor')
