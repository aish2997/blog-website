# Google OAuth Setup Guide for Django Blog

This guide walks you through setting up Google Sign-In for your Django blog using django-allauth.

---

## ✅ Completed Setup

The following has already been configured:

1. ✅ **django-allauth installed** (`requirements.txt`)
2. ✅ **Settings configured** (`portfolio/settings.py`)
3. ✅ **URLs configured** (`portfolio/urls.py`)
4. ✅ **Comment model updated** to require authenticated users

---

## 📋 Next Steps

### Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one:
   - Click "Select a project" → "New Project"
   - Name: `blog-website-oauth`
   - Click "Create"

3. Enable Google+ API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API"
   - Click "Enable"

4. Create OAuth Consent Screen:
   - Go to "APIs & Services" → "OAuth consent screen"
   - Select "External" (for public blog)
   - Fill in:
     - **App name**: Your Blog Name
     - **User support email**: your-email@gmail.com
     - **Developer contact**: your-email@gmail.com
   - Click "Save and Continue"
   - Skip "Scopes" (default is fine)
   - Click "Save and Continue"

5. Create OAuth Client ID:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Web application"
   - Name: `Django Blog OAuth`
   - **Authorized JavaScript origins**:
     ```
     http://localhost:8000
     https://your-cloudrun-url.run.app
     ```
   - **Authorized redirect URIs**:
     ```
     http://localhost:8000/accounts/google/login/callback/
     https://your-cloudrun-url.run.app/accounts/google/login/callback/
     ```
   - Click "Create"
   - **SAVE the Client ID and Client Secret** (you'll need these!)

---

### Step 2: Install django-allauth and Run Migrations

```bash
cd app

# Install dependencies (if not already done)
pip install -r requirements.txt

# Run migrations to create allauth tables
python manage.py migrate

# Expected output:
#   Running migrations:
#     Applying account.0001_initial... OK
#     Applying account.0002_email_max_length... OK
#     Applying sites.0001_initial... OK
#     Applying sites.0002_alter_domain_unique... OK
#     Applying socialaccount.0001_initial... OK
#     Applying socialaccount.0002_token_max_lengths... OK
#     Applying socialaccount.0003_extra_data_default_dict... OK
#     Applying socialaccount.0004_app_provider_id_settings... OK
#     Applying socialaccount.0005_socialtoken_nullable_app... OK
#     Applying socialaccount.0006_alter_socialaccount_extra_data... OK
#     Applying comments.0002_remove_comment_author_email_... OK  (Comment model changes)

# Create migrations for Comment model (if not done automatically)
python manage.py makemigrations comments
python manage.py migrate
```

---

### Step 3: Configure Google Provider in Django Admin

1. Start the development server:
   ```bash
   python manage.py runserver
   ```

2. Go to http://localhost:8000/admin/

3. Navigate to "Sites" → Click on "example.com"
   - Change **Domain name** to: `localhost:8000`
   - Change **Display name** to: `Local Development`
   - Click "Save"

4. Navigate to "Social applications" → Click "Add social application"
   - **Provider**: Google
   - **Name**: Google OAuth
   - **Client id**: [Paste your Google Client ID from Step 1]
   - **Secret key**: [Paste your Google Client Secret from Step 1]
   - **Sites**: Select "localhost:8000" and move it to "Chosen sites"
   - Click "Save"

---

### Step 4: Test Google Sign-In Locally

1. Go to http://localhost:8000/accounts/google/login/

2. You should be redirected to Google's Sign-In page

3. Select your Google account

4. You'll be redirected back to your blog

5. Check if you're logged in:
   - Go to http://localhost:8000/admin/
   - Go to "Users" → You should see your Google account listed

---

### Step 5: Update Comment Views and Forms

Update `app/apps/comments/views.py` to require authentication:

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Comment
from .forms import CommentForm

@login_required
def add_comment(request, content_type_id, object_id):
    """Add a comment (requires login)"""
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.content_type_id = content_type_id
            comment.object_id = object_id

            # Get Google profile picture
            google_account = request.user.socialaccount_set.filter(provider='google').first()
            if google_account:
                comment.profile_picture_url = google_account.extra_data.get('picture', '')

            comment.save()
            messages.success(request, 'Your comment has been posted!')
            return redirect(request.META.get('HTTP_REFERER', '/'))

    return redirect('/')

@login_required
def edit_comment(request, comment_id):
    """Edit own comment"""
    comment = get_object_or_404(Comment, id=comment_id)

    # Check if user owns this comment
    if not comment.can_edit(request.user):
        return HttpResponseForbidden("You cannot edit this comment.")

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.is_edited = True
            comment.save()
            messages.success(request, 'Comment updated successfully!')
            return redirect(request.META.get('HTTP_REFERER', '/'))
    else:
        form = CommentForm(instance=comment)

    return render(request, 'comments/edit_comment.html', {'form': form, 'comment': comment})

@login_required
def delete_comment(request, comment_id):
    """Delete own comment"""
    comment = get_object_or_404(Comment, id=comment_id)

    # Check if user can delete this comment
    if not comment.can_delete(request.user):
        return HttpResponseForbidden("You cannot delete this comment.")

    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Comment deleted successfully!')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    return render(request, 'comments/confirm_delete.html', {'comment': comment})
```

Update `app/apps/comments/forms.py`:

```python
from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'parent']  # Removed author_name and author_email
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your comment here...'
            }),
            'parent': forms.HiddenInput(),
        }
```

---

### Step 6: Update Templates

Create `templates/base.html` with Google Sign-In button:

```html
{% load socialaccount %}

<!-- In your header/navbar -->
{% if user.is_authenticated %}
    <!-- Show user profile -->
    <div class="user-profile">
        <img src="{% if user.socialaccount_set.all.0.get_avatar_url %}{{ user.socialaccount_set.all.0.get_avatar_url }}{% else %}https://www.gravatar.com/avatar/default?d=identicon&s=40{% endif %}"
             alt="{{ user.get_full_name }}"
             class="user-avatar">
        <span>{{ user.get_full_name|default:user.email }}</span>
        <a href="{% url 'account_logout' %}">Sign Out</a>
    </div>
{% else %}
    <!-- Show Sign In button -->
    <a href="{% provider_login_url 'google' %}" class="btn btn-google">
        <img src="https://developers.google.com/identity/images/g-logo.png" alt="Google">
        Sign in with Google
    </a>
{% endif %}
```

Update comment display template:

```html
<!-- templates/comments/comment_list.html -->
{% for comment in comments %}
<div class="comment {% if comment.parent %}comment-reply{% endif %}">
    <div class="comment-header">
        <img src="{{ comment.get_avatar_url }}" alt="{{ comment.get_author_name }}" class="comment-avatar">
        <div class="comment-meta">
            <strong>{{ comment.get_author_name }}</strong>
            <span class="comment-date">{{ comment.created_at|timesince }} ago</span>
            {% if comment.is_edited %}
                <span class="edited-badge">(edited {{ comment.edited_at|timesince }} ago)</span>
            {% endif %}
        </div>

        <!-- Edit/Delete buttons for own comments -->
        {% if user.is_authenticated and comment.can_edit user %}
            <div class="comment-actions">
                <a href="{% url 'edit_comment' comment.id %}" class="btn-edit">Edit</a>
                <a href="{% url 'delete_comment' comment.id %}" class="btn-delete">Delete</a>
            </div>
        {% endif %}
    </div>

    <div class="comment-content">
        {{ comment.content|linebreaks }}
    </div>

    <div class="comment-footer">
        <button class="btn-reply" data-comment-id="{{ comment.id }}">Reply</button>
    </div>

    <!-- Nested replies -->
    {% if comment.replies.all %}
        <div class="comment-replies">
            {% for reply in comment.replies.all %}
                <!-- Recursive render of replies -->
            {% endfor %}
        </div>
    {% endif %}
</div>
{% endfor %}
```

Update comment form template to require login:

```html
<!-- templates/comments/comment_form.html -->
{% load socialaccount %}

{% if user.is_authenticated %}
    <form method="post" action="{% url 'add_comment' content_type.id object.id %}" class="comment-form">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit" class="btn btn-primary">Post Comment</button>
    </form>
{% else %}
    <div class="login-prompt">
        <p>Please sign in with Google to post a comment</p>
        <a href="{% provider_login_url 'google' %}?next={{ request.path }}" class="btn btn-google">
            <img src="https://developers.google.com/identity/images/g-logo.png" alt="Google">
            Sign in with Google
        </a>
    </div>
{% endif %}
```

---

### Step 7: Update CommentAdmin

Update `app/apps/comments/admin.py`:

```python
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_short', 'content_object_link', 'is_approved',
                    'is_featured', 'is_edited', 'created_at']  # Changed from author_name to user
    list_filter = ['is_approved', 'is_featured', 'is_spam', 'is_edited', 'created_at', 'content_type']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'content', 'ip_address']  # Changed from author_name/email
    list_editable = ['is_approved', 'is_featured', 'is_spam']
    readonly_fields = ['content_type', 'object_id', 'content_object', 'user', 'profile_picture_url',
                       'ip_address', 'user_agent', 'created_at', 'updated_at', 'edited_at',
                       'approved_at', 'approved_by']

    fieldsets = (
        ('Comment Content', {
            'fields': ('user', 'profile_picture_url', 'content', 'parent')
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id', 'content_object'),
        }),
        ('Moderation', {
            'fields': ('is_approved', 'is_featured', 'is_spam', 'approved_at', 'approved_by')
        }),
        ('Edit History', {
            'fields': ('is_edited', 'edited_at'),
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

    def user_profile_pic(self, obj):
        """Display user's Google profile picture in admin"""
        if obj.profile_picture_url:
            return format_html('<img src="{}" style="width: 40px; height: 40px; border-radius: 50%;">', obj.profile_picture_url)
        return '-'
    user_profile_pic.short_description = 'Profile Pic'
```

---

### Step 8: Deploy to Cloud Run

1. **Add environment variables** to Cloud Run:
   ```bash
   # Add Google OAuth credentials to Secret Manager
   echo -n "YOUR_GOOGLE_CLIENT_ID" | gcloud secrets create google-oauth-client-id --data-file=-
   echo -n "YOUR_GOOGLE_CLIENT_SECRET" | gcloud secrets create google-oauth-client-secret --data-file=-

   # Update Cloud Run service
   gcloud run services update blog-website \
     --region us-central1 \
     --update-secrets=GOOGLE_OAUTH_CLIENT_ID=google-oauth-client-id:latest,GOOGLE_OAUTH_CLIENT_SECRET=google-oauth-client-secret:latest
   ```

2. **Update Site in Django Admin (Production)**:
   - After deploying, go to your production admin: `https://your-app.run.app/admin/`
   - Navigate to "Sites"
   - Change domain to: `your-app.run.app`
   - Change display name to: `Production`

3. **Add Social Application (Production)**:
   - Go to "Social applications" → Add
   - Provider: Google
   - Name: Google OAuth (Production)
   - Client ID: [From Google Cloud Console]
   - Secret: [From Google Cloud Console]
   - Sites: Select "your-app.run.app"

---

## 🎉 Success Checklist

- [ ] Google OAuth credentials created
- [ ] Migrations run successfully
- [ ] Site configured in Django admin
- [ ] Social application configured
- [ ] Test login works locally
- [ ] Comment views updated
- [ ] Templates updated with Sign-In button
- [ ] CommentAdmin updated
- [ ] Environment variables added to Cloud Run
- [ ] Production site configured
- [ ] Test Sign-In works in production
- [ ] Test commenting works
- [ ] Test edit/delete works

---

## 🔒 Security Best Practices

1. **Never commit OAuth secrets** to git
2. **Use environment variables** for all credentials
3. **Enable HTTPS** in production (Cloud Run does this automatically)
4. **Set `SESSION_COOKIE_SECURE = True`** in production
5. **Regularly rotate** OAuth secrets

---

## 🐛 Troubleshooting

### Error: "Redirect URI mismatch"
**Solution**: Make sure the redirect URI in Google Console exactly matches:
```
http://localhost:8000/accounts/google/login/callback/
```

### Error: "Site matching query does not exist"
**Solution**: Run migrations and configure Site in admin:
```bash
python manage.py migrate
# Then configure in admin at /admin/sites/site/
```

### Profile picture not showing
**Solution**: Check that `SOCIALACCOUNT_STORE_TOKENS = True` and `FETCH_USERINFO = True` are set in settings.py

---

## 📚 Additional Resources

- [django-allauth Documentation](https://django-allauth.readthedocs.io/)
- [Google OAuth Setup](https://developers.google.com/identity/protocols/oauth2)
- [Django Sites Framework](https://docs.djangoproject.com/en/4.2/ref/contrib/sites/)

---

**Next**: After completing these steps, your blog will have full Google Sign-In authentication with user comments!
