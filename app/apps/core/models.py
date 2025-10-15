from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Profile(models.Model):
    """Main profile model for the portfolio owner"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=200)
    title = models.CharField(max_length=200, help_text="e.g., Full Stack Developer")
    bio = models.TextField(help_text="Short bio for homepage")
    about_me = models.TextField(help_text="Detailed about section")
    profile_image = models.ImageField(upload_to='profile/', blank=True, null=True)

    # Social links
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    email = models.EmailField()

    # SEO
    meta_description = models.CharField(max_length=160, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return self.full_name


class Skill(models.Model):
    """Skills for resume/portfolio"""
    SKILL_TYPES = (
        ('language', 'Programming Language'),
        ('framework', 'Framework'),
        ('tool', 'Tool'),
        ('database', 'Database'),
        ('soft', 'Soft Skill'),
        ('other', 'Other'),
    )

    name = models.CharField(max_length=100)
    skill_type = models.CharField(max_length=20, choices=SKILL_TYPES)
    proficiency = models.IntegerField(default=50, help_text="Proficiency percentage (0-100)")
    icon = models.CharField(max_length=100, blank=True, help_text="Font Awesome icon class or image")
    order = models.IntegerField(default=0, help_text="Display order")
    is_featured = models.BooleanField(default=False, help_text="Show on homepage")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Education(models.Model):
    """Education entries for CV"""
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    gpa = models.CharField(max_length=10, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-end_date', '-start_date']
        verbose_name_plural = 'Education'

    def __str__(self):
        return f"{self.degree} - {self.institution}"


class WorkExperience(models.Model):
    """Work experience entries for CV"""
    company = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    employment_type = models.CharField(max_length=50, choices=[
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance'),
    ])
    location = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(help_text="Job responsibilities and achievements (supports Markdown)")
    technologies_used = models.CharField(max_length=500, blank=True, help_text="Comma-separated list")
    company_logo = models.ImageField(upload_to='companies/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_current', '-end_date', '-start_date']
        verbose_name_plural = 'Work Experiences'

    def __str__(self):
        return f"{self.position} at {self.company}"

    def get_technologies_list(self):
        """Return technologies as a list"""
        if self.technologies_used:
            return [tech.strip() for tech in self.technologies_used.split(',')]
        return []


class Certification(models.Model):
    """Professional certifications"""
    name = models.CharField(max_length=200)
    issuing_organization = models.CharField(max_length=200)
    issue_date = models.DateField()
    expiry_date = models.DateField(blank=True, null=True)
    credential_id = models.CharField(max_length=200, blank=True)
    credential_url = models.URLField(blank=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.name} - {self.issuing_organization}"


class Achievement(models.Model):
    """Awards and achievements"""
    title = models.CharField(max_length=200)
    organization = models.CharField(max_length=200)
    date = models.DateField()
    description = models.TextField()
    url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.title


class CVDownload(models.Model):
    """Track CV downloads and views"""
    file = models.FileField(upload_to='cv/', help_text="Upload your CV in PDF format")
    version = models.CharField(max_length=20, default="1.0")
    is_active = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(blank=True, null=True)
    last_downloaded = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'CV File'
        verbose_name_plural = 'CV Files'

    def __str__(self):
        return f"CV v{self.version} - {self.created_at.strftime('%Y-%m-%d')}"

    def increment_view_count(self):
        self.view_count += 1
        self.last_viewed = timezone.now()
        self.save(update_fields=['view_count', 'last_viewed'])

    def increment_download_count(self):
        self.download_count += 1
        self.last_downloaded = timezone.now()
        self.save(update_fields=['download_count', 'last_downloaded'])
