from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.db.models import Q
from .models import Project
from apps.comments.models import Comment


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

        # Get approved top-level comments (no parent)
        # Use prefetch_related to efficiently load all nested replies
        context['comments'] = Comment.objects.filter(
            content_type__app_label='projects',
            content_type__model='project',
            object_id=self.object.id,
            is_approved=True,
            parent=None
        ).select_related('user').prefetch_related(
            'replies__user',
            'replies__replies__user',
            'replies__replies__replies__user'
        ).order_by('-is_featured', '-created_at')

        return context

    def post(self, request, *args, **kwargs):
        """Handle comment submission, deletion, editing, and replies"""
        self.object = self.get_object()

        # Check if user is authenticated
        if not request.user.is_authenticated:
            messages.error(request, 'You must be signed in to comment.')
            return redirect('account_login')

        # Handle delete action
        action = request.POST.get('action', '')
        if action == 'delete':
            comment_id = request.POST.get('comment_id')
            try:
                comment = Comment.objects.get(id=comment_id, user=request.user)
                comment.delete()
                messages.success(request, 'Your comment has been deleted.')
            except Comment.DoesNotExist:
                messages.error(request, 'Comment not found or you do not have permission to delete it.')
            return redirect('projects:detail', slug=self.object.slug)

        # Handle edit action
        if action == 'edit':
            comment_id = request.POST.get('comment_id')
            content = request.POST.get('content', '').strip()

            if not content:
                messages.error(request, 'Comment content cannot be empty.')
                return redirect('projects:detail', slug=self.object.slug)

            try:
                from django.utils import timezone
                comment = Comment.objects.get(id=comment_id, user=request.user)
                comment.content = content
                comment.is_edited = True
                comment.edited_at = timezone.now()
                comment.save()
                messages.success(request, 'Your comment has been updated.')
            except Comment.DoesNotExist:
                messages.error(request, 'Comment not found or you do not have permission to edit it.')
            return redirect('projects:detail', slug=self.object.slug)

        # Get form data for creating comment or reply
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent_id', '').strip()

        # Validate required fields
        if content:
            # Get content type for the project
            content_type = ContentType.objects.get_for_model(Project)

            # Get user's profile picture from Google OAuth if available
            profile_picture_url = ''
            try:
                social_account = request.user.socialaccount_set.filter(provider='google').first()
                if social_account and social_account.extra_data:
                    profile_picture_url = social_account.extra_data.get('picture', '')
            except Exception:
                pass

            # Get parent comment if this is a reply
            parent = None
            if parent_id:
                try:
                    parent = Comment.objects.get(id=parent_id)
                except Comment.DoesNotExist:
                    pass

            # Create the comment or reply (auto-approved for authenticated users)
            Comment.objects.create(
                content_type=content_type,
                object_id=self.object.id,
                user=request.user,
                profile_picture_url=profile_picture_url,
                content=content,
                parent=parent,
                is_approved=True  # Auto-approve authenticated users
            )

            # Add success message
            if parent:
                messages.success(request, 'Your reply has been posted!')
            else:
                messages.success(request, 'Your comment has been posted!')
        else:
            # Add error message
            messages.error(request, 'Please enter a comment.')

        # Redirect back to the project detail page
        return redirect('projects:detail', slug=self.object.slug)
