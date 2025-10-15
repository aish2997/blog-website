# Portfolio Blog Website - Django Cloud Run

A production-grade portfolio website built with Django, designed for deployment on Google Cloud Run with Cloud SQL (PostgreSQL) and Cloud Storage.

## Features

### Core Functionality
- **Portfolio Landing Page**: Professional homepage with profile, skills, and featured content
- **Blog System**: Full-featured blog with markdown support, categories, and tags
- **Projects Showcase**: Display projects with GitHub integration, tech stacks, and galleries
- **CV/Resume Section**: Dynamic resume with work experience, education, certifications
  - View counter for CV section
  - Download tracking
  - Last updated timestamp
- **Comment System**: Moderated comments with approval workflow
- **Analytics**: Built-in visitor tracking and page view analytics
- **Admin Panel**: Comprehensive Django admin with markdown editor

### Technical Features
- **Cloud-Native Architecture**: Optimized for Google Cloud Platform
- **Containerized**: Docker-based deployment for Cloud Run
- **Scalable Storage**: Cloud Storage for media files
- **Database**: Cloud SQL (PostgreSQL) for reliability
- **Security**: Secret Manager integration, HTTPS enforced
- **SEO Optimized**: Meta tags, sitemaps, structured data
- **Responsive Design**: Mobile-first approach
- **Markdown Support**: Write blog posts and project descriptions in Markdown

## Project Structure

```
blog-website/
├── apps/                   # Django applications
│   ├── core/              # Profile, Skills, CV models
│   ├── blog/              # Blog posts and categories
│   ├── projects/          # Project showcase
│   ├── comments/          # Comment system with moderation
│   └── analytics/         # Visitor tracking and statistics
├── portfolio/             # Django project settings
├── templates/             # HTML templates
├── static/                # CSS, JS, images
├── media/                 # User-uploaded files
├── terraform/             # Infrastructure as Code
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── cloudbuild.yaml       # CI/CD pipeline
├── deploy.sh             # Deployment script
└── manage.py             # Django management script
```

## Quick Start - Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd blog-website
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Site: http://localhost:8000
   - Admin: http://localhost:8000/admin

## Deployment to Google Cloud Run

### Prerequisites
- Google Cloud Project with billing enabled
- gcloud CLI installed and configured
- Docker installed (optional, for local testing)

### Deployment Steps

1. **Set your project ID**
   ```bash
   export GCP_PROJECT_ID="your-project-id"
   ```

2. **Run the deployment script**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

   This script will:
   - Enable required GCP APIs
   - Create Cloud SQL instance
   - Set up Cloud Storage bucket
   - Configure secrets in Secret Manager
   - Build and deploy to Cloud Run
   - Run database migrations

3. **Manual deployment with gcloud**
   ```bash
   # Build and push image
   gcloud builds submit --tag gcr.io/${GCP_PROJECT_ID}/portfolio

   # Deploy to Cloud Run
   gcloud run deploy portfolio \
     --image gcr.io/${GCP_PROJECT_ID}/portfolio \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

## Configuration

### Environment Variables

Key environment variables for production:

- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `CLOUD_SQL_CONNECTION_NAME`: Cloud SQL instance connection name
- `DB_NAME`: Database name (default: portfolio)
- `DB_USER`: Database user (default: postgres)
- `GCS_BUCKET_NAME`: Cloud Storage bucket for media files
- `DJANGO_SETTINGS_MODULE`: Set to `portfolio.settings_production`

### Secrets (stored in Secret Manager)

- `DJANGO_SECRET_KEY`: Django secret key
- `DB_PASSWORD`: Database password
- `SENDGRID_API_KEY`: Email service API key

## Admin Panel Usage

1. **Access admin panel**: `https://your-domain.run.app/admin/`

2. **Key sections**:
   - **Profile**: Manage your personal information
   - **Blog Posts**: Create and manage blog posts with markdown
   - **Projects**: Showcase your projects
   - **Comments**: Moderate user comments
   - **Analytics**: View site statistics
   - **CV/Resume**: Manage work experience, education, skills

3. **Content Management**:
   - Use the markdown editor for blog posts and project descriptions
   - Upload images for blog posts and projects
   - Tag content for better organization
   - Set posts/projects as featured for homepage display

## Features in Detail

### Blog System
- Markdown editor with live preview
- Categories and tags
- Draft/Published states
- Featured posts
- View counting
- Reading time estimation
- SEO metadata

### Project Showcase
- GitHub repository integration
- Technology stack display
- Project status tracking
- Image galleries
- Live demo links

### CV/Resume Section
- Work experience with timeline
- Education history
- Skills with proficiency levels
- Certifications
- Achievements
- PDF download tracking
- View counter

### Comment System
- Anonymous commenting (with optional email)
- Nested replies
- Admin moderation queue
- Spam detection
- Comment flagging

### Analytics
- Unique visitor tracking
- Page view statistics
- Popular content tracking
- Search query logging
- Event tracking (downloads, clicks)

## Maintenance

### Database Backup
```bash
# Create backup
gcloud sql backups create --instance=portfolio-db

# List backups
gcloud sql backups list --instance=portfolio-db
```

### Update Application
1. Make code changes
2. Commit to repository
3. Cloud Build will automatically deploy (if configured)
4. Or run `./deploy.sh` manually

### Monitor Performance
- Cloud Run metrics: CPU, memory, request count
- Cloud SQL metrics: connections, storage
- Error reporting in Cloud Console

## Security Best Practices

1. **Keep secrets secure**: Never commit secrets to repository
2. **Update dependencies**: Regularly update Python packages
3. **Use HTTPS**: Cloud Run provides HTTPS by default
4. **Set up IAM**: Use principle of least privilege
5. **Enable audit logs**: Track admin actions
6. **Regular backups**: Automate database backups

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check Cloud SQL instance is running
   - Verify connection name in environment variables
   - Check IAM permissions

2. **Media files not loading**
   - Verify Cloud Storage bucket exists
   - Check bucket permissions (public read)
   - Verify MEDIA_URL setting

3. **Migration errors**
   - Ensure database exists
   - Check database credentials
   - Run migrations manually if needed

### Logs
```bash
# View Cloud Run logs
gcloud run services logs read portfolio

# View Cloud SQL logs
gcloud sql operations list --instance=portfolio-db
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

[Your License Here]

## Contact

For questions or support, please contact [your-email@example.com]