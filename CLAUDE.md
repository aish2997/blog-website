# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django-based portfolio and blog website designed for Google Cloud Run deployment. It features a blog system with markdown support, project showcase, CV/resume section, comments, and built-in analytics.

## Project Structure

```
.
├── app/                    # Django application code
│   ├── apps/              # Django apps (core, blog, projects, etc.)
│   ├── portfolio/         # Django project settings
│   ├── templates/         # HTML templates
│   ├── static/           # Static assets
│   ├── manage.py         # Django management script
│   └── requirements.txt  # Python dependencies
├── terraform/            # Infrastructure as Code
│   ├── bootstrap/        # Initial GCP setup
│   └── infrastructure/   # Application infrastructure
├── docker/              # Docker configuration
│   └── Dockerfile       # Container definition
└── .github/            # GitHub Actions workflows
    └── workflows/      # CI/CD pipelines
```

## Key Commands

### Development Setup
```bash
# Navigate to app directory
cd app

# Activate virtual environment (from project root)
source ../venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser

# Run development server
python manage.py runserver
# Access at: http://localhost:8000
# Admin at: http://localhost:8000/admin
```

### Testing
```bash
# From app directory
cd app

# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test apps.blog
python manage.py test apps.projects
python manage.py test apps.core
python manage.py test apps.comments
python manage.py test apps.analytics

# Run tests with coverage
coverage run --source='apps' manage.py test
coverage report
```

### Static Files and Database
```bash
# From app directory
cd app

# Collect static files (required before deployment)
python manage.py collectstatic --noinput

# Create database backup (SQLite in development)
python manage.py dbbackup

# Load initial data fixtures (if available)
python manage.py loaddata initial_data
```

### Deployment
```bash
# Deploy to Google Cloud Run
./deploy.sh

# Build Docker image locally
docker build -t portfolio .

# Run Docker container locally
docker run -p 8080:8080 portfolio
```

## Architecture

### Django Apps Structure

The project follows a modular app-based architecture under the `app/apps/` directory:

1. **apps.core**: Central app containing Profile, Skills, CV/Resume models and site-wide configurations. Provides the main landing page and context processors for global settings.

2. **apps.blog**: Full-featured blog with BlogPost and Category models, markdown support via MarkdownxField, tagging with django-taggit, and SEO optimization features.

3. **apps.projects**: Project showcase system with GitHub integration, technology stack tracking, project status management, and image galleries.

4. **apps.comments**: Moderated commenting system for blog posts and projects with approval workflow and spam protection.

5. **apps.analytics**: Built-in analytics for tracking page views, unique visitors, and user interactions without external dependencies.

### Key Technical Decisions

- **Database**: SQLite for both development and production (cost-effective for portfolio site)
  - Production uses `/tmp/db.sqlite3` (the only writable directory in Cloud Run)
  - SQLite optimizations applied via Django signal in `apps.core.apps` (WAL mode, increased cache, etc.)
  - Database is synced to/from GCS for persistence across container restarts
  - Single Gunicorn worker configured to avoid SQLite concurrency issues
- **Media Storage**: Local filesystem in development, Google Cloud Storage in production (optional)
- **Static Files**: Served via WhiteNoise middleware with compression
- **Markdown Processing**: markdownx for editing, markdownify for rendering
- **Authentication**: Django's built-in auth system
- **Admin Interface**: Customized Django admin with markdown editor integration

### URL Structure

- `/` - Homepage (from apps.core)
- `/blog/` - Blog listing and posts (from apps.blog)
- `/projects/` - Project showcase (from apps.projects)
- `/cv/` - CV/Resume page (handled by apps.core)
- `/admin/` - Django admin panel
- `/markdownx/` - Markdown editor endpoints

### Environment Configuration

The project uses django-environ for configuration management. Key settings:

- Development: Uses `app/.env` file with DEBUG=True, SQLite database
- Production: Uses `app/portfolio/settings_production.py` module with Secret Manager integration

Required environment variables:
- `SECRET_KEY` - Django secret key (or uses Secret Manager if GCP_PROJECT_ID is set)
- `DEBUG` - Debug mode (True/False)
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `DATABASE_PATH` - Path to SQLite database (defaults to /tmp/db.sqlite3 in production)
- `GCS_BUCKET_MEDIA` - Google Cloud Storage bucket for media files (optional)
- `GCS_BUCKET_STATIC` - Google Cloud Storage bucket for static files (optional)
- `GCP_PROJECT_ID` - GCP project ID for Secret Manager integration (optional)

### Model Relationships

- BlogPost → Category (ForeignKey)
- BlogPost → User (author)
- BlogPost → Tags (ManyToMany via taggit)
- Project → Technologies (ManyToMany)
- Comment → BlogPost/Project (GenericForeignKey)
- Profile → User (OneToOne)

### Frontend Integration

The project uses server-side rendered templates with:
- Template inheritance from `base.html`
- Context processors for global data
- Markdown rendering in templates via markdownify filter
- Static files served from `/static/` directory

## Important Notes

- The development server automatically runs on port 8000
- Media files are stored in `app/media/` directory (gitignored)
- Database file `app/db.sqlite3` is gitignored for development
- Admin customizations are in each app's `admin.py` file
- SEO features include meta descriptions, Open Graph tags, and sitemaps
- The project includes Docker configuration in `docker/` for Cloud Run deployment
- Terraform configuration exists in `terraform/` for infrastructure as code
- All Django application code is isolated in the `app/` directory for cleaner Docker builds