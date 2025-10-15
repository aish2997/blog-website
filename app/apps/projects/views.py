from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Project


class ProjectListView(ListView):
    """List all published projects"""
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        queryset = Project.objects.filter(is_public=True)

        # Filter by technology if provided
        tech = self.request.GET.get('tech')
        if tech:
            queryset = queryset.filter(technologies__name__in=[tech])

        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(short_description__icontains=search_query)
            )

        return queryset.order_by('-featured', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all unique technologies
        all_projects = Project.objects.filter(is_public=True)
        technologies = set()
        for project in all_projects:
            for tech in project.technologies.all():
                technologies.add(tech.name)

        context['technologies'] = sorted(list(technologies))
        context['featured_projects'] = Project.objects.filter(
            featured=True, is_public=True
        )[:3]

        return context


class ProjectDetailView(DetailView):
    """Display a single project"""
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Project.objects.filter(is_public=True)

    def get_object(self):
        obj = super().get_object()

        # Increment view count only once per session per project
        session_key = f'project_viewed_{obj.id}'
        if not self.request.session.get(session_key):
            obj.increment_view_count()
            self.request.session[session_key] = True
            self.request.session.set_expiry(86400)  # Expire after 24 hours

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get related projects (same technologies)
        current_techs = self.object.technologies.all()
        related_projects = Project.objects.filter(
            technologies__in=current_techs,
            is_public=True
        ).exclude(id=self.object.id).distinct()[:3]

        context['related_projects'] = related_projects

        return context
