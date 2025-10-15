from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.db.models import Q
from .models import BlogPost, Category
from apps.comments.models import Comment


class BlogListView(ListView):
    """List all published blog posts"""
    model = BlogPost
    template_name = 'blog/blog_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        queryset = BlogPost.objects.filter(status='published').select_related(
            'author', 'category'
        ).prefetch_related('tags')

        # Filter by category if provided
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # Filter by tag if provided
        tag = self.request.GET.get('tag')
        if tag:
            queryset = queryset.filter(tags__name__in=[tag])

        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(excerpt__icontains=search_query)
            )

        return queryset.order_by('-published_date', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['recent_posts'] = BlogPost.objects.filter(
            status='published'
        ).order_by('-published_date')[:5]

        # Add category info if filtering by category
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['current_category'] = get_object_or_404(Category, slug=category_slug)

        return context


class BlogDetailView(DetailView):
    """Display a single blog post"""
    model = BlogPost
    template_name = 'blog/blog_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return BlogPost.objects.filter(status='published').select_related(
            'author', 'category'
        ).prefetch_related('tags')

    def get_object(self):
        obj = super().get_object()

        # Increment view count only once per session per blog post
        session_key = f'blog_viewed_{obj.id}'
        if not self.request.session.get(session_key):
            obj.increment_view_count()
            self.request.session[session_key] = True
            self.request.session.set_expiry(86400)  # Expire after 24 hours

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get approved comments
        context['comments'] = Comment.objects.filter(
            content_type__app_label='blog',
            content_type__model='blogpost',
            object_id=self.object.id,
            is_approved=True,
            parent=None
        ).select_related('parent').order_by('-is_featured', '-created_at')

        # Get related posts
        context['related_posts'] = self.object.related_posts

        return context

    def post(self, request, *args, **kwargs):
        """Handle comment submission"""
        self.object = self.get_object()

        # Get form data
        author_name = request.POST.get('author_name', '').strip()
        author_email = request.POST.get('author_email', '').strip()
        content = request.POST.get('content', '').strip()

        # Validate required fields
        if author_name and author_email and content:
            # Get content type for the blog post
            content_type = ContentType.objects.get_for_model(BlogPost)

            # Create the comment (not approved by default)
            Comment.objects.create(
                content_type=content_type,
                object_id=self.object.id,
                author_name=author_name,
                author_email=author_email,
                content=content,
                is_approved=False  # Requires admin approval
            )

            # Add success message
            messages.success(request, 'Your comment has been submitted and is awaiting moderation.')
        else:
            # Add error message
            messages.error(request, 'Please fill in all required fields.')

        # Redirect back to the post detail page
        return redirect('blog:detail', slug=self.object.slug)
