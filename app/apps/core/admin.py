from django.contrib import admin
from .models import (
    Profile, Skill, Education, WorkExperience,
    Certification, Achievement, CVDownload
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'title', 'email', 'created_at']
    search_fields = ['full_name', 'title', 'email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'full_name', 'title', 'email', 'profile_image')
        }),
        ('Bio', {
            'fields': ('bio', 'about_me')
        }),
        ('Social Links', {
            'fields': ('github_url', 'linkedin_url', 'twitter_url')
        }),
        ('SEO', {
            'fields': ('meta_description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'skill_type', 'proficiency', 'is_featured', 'order']
    list_filter = ['skill_type', 'is_featured']
    search_fields = ['name']
    list_editable = ['proficiency', 'is_featured', 'order']
    ordering = ['order', 'name']


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ['degree', 'institution', 'field_of_study', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current', 'start_date']
    search_fields = ['institution', 'degree', 'field_of_study']
    ordering = ['-end_date', '-start_date']


@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = ['position', 'company', 'employment_type', 'start_date', 'end_date', 'is_current']
    list_filter = ['employment_type', 'is_current']
    search_fields = ['position', 'company', 'technologies_used']
    ordering = ['-is_current', '-end_date', '-start_date']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Position Details', {
            'fields': ('company', 'position', 'employment_type', 'location', 'company_logo')
        }),
        ('Duration', {
            'fields': ('start_date', 'end_date', 'is_current')
        }),
        ('Description', {
            'fields': ('description', 'technologies_used')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ['name', 'issuing_organization', 'issue_date', 'expiry_date']
    list_filter = ['issuing_organization', 'issue_date']
    search_fields = ['name', 'issuing_organization', 'credential_id']
    ordering = ['-issue_date']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['title', 'organization', 'date']
    list_filter = ['organization', 'date']
    search_fields = ['title', 'organization', 'description']
    ordering = ['-date']


@admin.register(CVDownload)
class CVDownloadAdmin(admin.ModelAdmin):
    list_display = ['version', 'is_active', 'view_count', 'download_count', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    readonly_fields = ['view_count', 'download_count', 'last_viewed', 'last_downloaded', 'created_at', 'updated_at']
    actions = ['make_active', 'make_inactive']

    def make_active(self, request, queryset):
        # First deactivate all CVs
        CVDownload.objects.update(is_active=False)
        # Then activate selected
        queryset.update(is_active=True)
        self.message_user(request, "Selected CV(s) have been activated.")
    make_active.short_description = "Mark selected CV as active"

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, "Selected CV(s) have been deactivated.")
    make_inactive.short_description = "Mark selected CV as inactive"
