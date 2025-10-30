# Migration Guide: SQLite to Neon PostgreSQL

## Overview

This guide walks you through migrating your Django blog from SQLite (ephemeral storage on Cloud Run) to Neon PostgreSQL (persistent, serverless database).

## Why Migrate?

### The Root Cause of the Admin Error
The Server Error (500) when clicking "Comments" in Django admin on Cloud Run was caused by:

1. **Orphaned Comments**: Comments referencing deleted BlogPost/Project objects
2. **Ephemeral SQLite Database**: Database in `/tmp/` gets wiped on container restart
3. **Backup/Restore Issues**: GCS backup/restore process can leave inconsistent data
4. **Unsafe Admin Code**: The `content_object_link` method didn't handle null `content_object`

### Benefits of PostgreSQL (Neon)
- ✅ **Persistent storage**: Database survives container restarts
- ✅ **Better performance**: Handles concurrent requests efficiently
- ✅ **Referential integrity**: Better support for foreign keys and constraints
- ✅ **Serverless scaling**: Auto-scales to zero when not in use
- ✅ **Database branching**: Create dev/staging copies instantly
- ✅ **Cost-effective**: Pay only for what you use

---

## Prerequisites

- [x] Neon account (sign up at https://neon.tech)
- [x] Access to your Cloud Run service
- [x] gcloud CLI installed and authenticated
- [x] Local copy of your current SQLite database (for data migration)

---

## Step 1: Set Up Neon PostgreSQL

### 1.1 Create Neon Project

1. Go to https://console.neon.tech
2. Click "Create Project"
3. Choose:
   - **Project name**: `blog-website-prod`
   - **Region**: Choose closest to your Cloud Run region (e.g., `us-east-1`)
   - **PostgreSQL version**: 16 (latest)
   - **Compute size**: 0.25 CU (perfect for blogs, scales to zero)

### 1.2 Get Connection String

After creating the project, you'll see a connection string like:
```
postgresql://username:password@ep-xxx-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require

postgresql://neondb_owner:npg_aE1htmuSIPA4@ep-falling-fire-agw51vny-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

**Save this connection string securely!** You'll need it in the next steps.

### 1.3 (Optional) Create Database Branches

Neon allows you to create branches for dev/staging:
```bash
# This creates a copy of your database for testing
neon branches create --name staging
```

---

## Step 2: Export Data from SQLite

### 2.1 Download Current SQLite Database from Cloud Run

If your database is backed up to GCS:
```bash
# Find your backup bucket
gsutil ls gs://your-media-bucket/db_backups/

# Download the latest backup
gsutil cp gs://your-media-bucket/db_backups/db.sqlite3 ./local-backup.sqlite3
```

Or download directly from a running Cloud Run container:
```bash
# Get the container name
gcloud run services list

# Copy database from container
gcloud run services proxy blog-website --region us-central1
# In another terminal:
# Connect to the service and download the file
```

### 2.2 Export Data to JSON

Run this locally with your SQLite database:
```bash
cd app

# Export all data to JSON
python manage.py dumpdata \
  --natural-foreign \
  --natural-primary \
  --exclude auth.permission \
  --exclude contenttypes \
  --indent 2 \
  > ../data-export.json

# Verify the export
ls -lh ../data-export.json
```

### 2.3 Clean Orphaned Comments (Important!)

Before importing to PostgreSQL, clean orphaned comments:
```bash
# Test what would be cleaned (dry run)
python manage.py clean_orphaned_comments --dry-run --verbose

# Actually clean them
python manage.py clean_orphaned_comments --verbose

# Export again after cleaning
python manage.py dumpdata \
  --natural-foreign \
  --natural-primary \
  --exclude auth.permission \
  --exclude contenttypes \
  --indent 2 \
  > ../data-export-cleaned.json
```

---

## Step 3: Configure PostgreSQL Locally (Test Migration)

### 3.1 Update Local Environment

Create a `.env.production` file locally:
```bash
# Database
DATABASE_URL=postgresql://username:password@ep-xxx-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require

# Other settings
DEBUG=False
DJANGO_SETTINGS_MODULE=portfolio.settings_production
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 3.2 Test Connection

```bash
# Set environment variables
export $(cat .env.production | xargs)

# Check Django can connect
python manage.py check --database default

# Expected output: System check identified no issues
```

### 3.3 Run Migrations

```bash
# Create schema in PostgreSQL
python manage.py migrate

# Expected output: All migrations applied successfully
```

### 3.4 Import Data

```bash
# Import the cleaned data
python manage.py loaddata ../data-export-cleaned.json

# Check data
python manage.py shell
>>> from apps.blog.models import BlogPost
>>> from apps.comments.models import Comment
>>> print(f"BlogPosts: {BlogPost.objects.count()}")
>>> print(f"Comments: {Comment.objects.count()}")
```

### 3.5 Test Locally

```bash
# Run the development server
python manage.py runserver

# Open browser to http://localhost:8000/admin
# Click on "Comments" - should work without errors!
```

---

## Step 4: Deploy to Cloud Run

### 4.1 Add DATABASE_URL to Cloud Run Secrets

Store the connection string in Google Secret Manager:
```bash
# Create the secret
echo -n "postgresql://username:password@ep-xxx-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require" | \
  gcloud secrets create database-url \
    --data-file=- \
    --replication-policy="automatic"

# Grant Cloud Run access
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding database-url \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 4.2 Update Cloud Run Service Configuration

Find your Cloud Run YAML or deployment script and add:
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: blog-website
spec:
  template:
    spec:
      containers:
      - image: gcr.io/your-project/blog-website
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-url
              key: latest
        # ... other env vars
```

Or using gcloud CLI:
```bash
gcloud run services update blog-website \
  --region us-central1 \
  --update-secrets=DATABASE_URL=database-url:latest
```

### 4.3 Deploy Updated Code

```bash
# Build and push new Docker image
gcloud builds submit --config cloudbuild.yaml

# Or redeploy the service
gcloud run deploy blog-website \
  --region us-central1 \
  --image gcr.io/your-project/blog-website:latest
```

### 4.4 Verify Deployment

```bash
# Check logs
gcloud run services logs read blog-website --region us-central1 --limit 50

# Look for:
# ✅ PostgreSQL database detected (DATABASE_URL is set)
# Running database migrations for PostgreSQL...
# Cleaning orphaned comments...
# Starting Gunicorn with PostgreSQL-optimized configuration (4 workers, 4 threads)...
```

### 4.5 Test in Production

1. Open your Cloud Run URL
2. Navigate to `/admin/`
3. Click on "Comments" → Should work without errors!
4. Check that orphaned comments show as "[Deleted BlogPost #123]"

---

## Step 5: Post-Migration Cleanup

### 5.1 Monitor Logs

```bash
# Monitor for any errors
gcloud run services logs tail blog-website --region us-central1

# Check for orphaned comment warnings
gcloud run services logs read blog-website \
  --region us-central1 \
  --filter="severity=WARNING AND textPayload:orphaned"
```

### 5.2 Performance Verification

The new setup should have:
- ✅ **Fewer database queries**: GenericPrefetch eliminates N+1 queries
- ✅ **Better concurrency**: 4 workers instead of 1
- ✅ **Persistent data**: No more ephemeral storage issues
- ✅ **Better admin UX**: Graceful handling of deleted objects

### 5.3 Remove SQLite Backup Logic (Optional)

Once you've verified PostgreSQL is working, you can:
1. Remove the `sync_database` management command
2. Clean up GCS backup bucket
3. Remove SQLite-related environment variables

---

## Step 6: Ongoing Maintenance

### 6.1 Regular Orphaned Comment Cleanup

Add a Cloud Scheduler job to clean orphaned comments weekly:
```bash
gcloud scheduler jobs create http cleanup-orphaned-comments \
  --schedule="0 2 * * 0" \
  --uri="https://your-blog.run.app/admin/cleanup-comments" \
  --http-method=POST \
  --oidc-service-account-email=your-service-account@your-project.iam.gserviceaccount.com
```

Or run manually:
```bash
gcloud run services execute blog-website \
  --region us-central1 \
  --command="python manage.py clean_orphaned_comments"
```

### 6.2 Database Backups with Neon

Neon provides automatic backups:
- **Daily backups**: Retained for 7 days (free tier) or 30 days (paid)
- **Point-in-time recovery**: Restore to any point in the last 7/30 days
- **Branch backups**: Create branches before major changes

To create a manual backup:
```bash
# Create a branch (instant snapshot)
neon branches create --name backup-$(date +%Y%m%d)
```

### 6.3 Monitoring Neon Performance

Check Neon console for:
- **Active connections**: Should stay under 20 for typical blog traffic
- **Query performance**: Identify slow queries
- **Storage usage**: Monitor database size growth

---

## Troubleshooting

### Issue: "Could not connect to server"

**Solution**: Check DATABASE_URL is set correctly
```bash
gcloud run services describe blog-website --region us-central1 --format="value(spec.template.spec.containers[0].env)"
```

### Issue: "FATAL: password authentication failed"

**Solution**: Reset Neon password
1. Go to Neon Console → Settings → Reset Password
2. Update the secret in Google Secret Manager:
```bash
echo -n "NEW_DATABASE_URL" | gcloud secrets versions add database-url --data-file=-
```

### Issue: "relation does not exist"

**Solution**: Migrations didn't run. Force migration:
```bash
# SSH into Cloud Run container
gcloud run services exec blog-website --region us-central1 -- python manage.py migrate
```

### Issue: Migration fails with "duplicate key value"

**Solution**: Your PostgreSQL database already has data. Either:
1. Drop and recreate the database in Neon Console
2. Or use `--fake-initial` flag:
```bash
python manage.py migrate --fake-initial
```

---

## Rollback Plan

If something goes wrong, you can quickly rollback:

### Option 1: Revert to SQLite
```bash
# Remove DATABASE_URL secret
gcloud run services update blog-website \
  --region us-central1 \
  --remove-secrets=DATABASE_URL

# Redeploy previous version
gcloud run services update-traffic blog-website \
  --region us-central1 \
  --to-revisions=PREVIOUS_REVISION=100
```

### Option 2: Restore Neon from Branch
```bash
# List branches
neon branches list

# Promote backup branch to main
neon branches set-as-primary --name backup-20250130
```

---

## Success Checklist

- [x] Neon PostgreSQL project created
- [x] Data exported from SQLite
- [x] Orphaned comments cleaned
- [x] Migration tested locally
- [x] DATABASE_URL added to Cloud Run secrets
- [x] Service deployed successfully
- [x] Comments admin page works without errors
- [x] All blog posts and comments visible
- [x] Performance improved (check with Django Debug Toolbar)
- [x] Logs show no errors for 24 hours

---

## Summary of Changes

This migration implemented the following architectural improvements:

### 1. **Fixed Admin Interface**
- `apps/comments/admin.py`: Safe null handling in `content_object_link()`
- `apps/comments/admin.py`: Added comprehensive error logging
- `apps/comments/admin.py`: Removed non-existent CSS reference
- `apps/comments/admin.py`: Optimized queryset with GenericPrefetch

### 2. **Database Architecture**
- `app/portfolio/settings_production.py`: PostgreSQL configuration with fallback to SQLite
- `docker/entrypoint.sh`: Detects database type and adjusts behavior
- `docker/entrypoint.sh`: Runs cleanup on PostgreSQL startup
- `docker/entrypoint.sh`: 4 workers for PostgreSQL vs 1 for SQLite

### 3. **Data Integrity**
- `apps/comments/signals.py`: Auto-delete comments when parent objects deleted
- `apps/comments/management/commands/clean_orphaned_comments.py`: Cleanup command
- `apps/blog/models.py`: Added GenericRelation field
- `apps/projects/models.py`: Added GenericRelation field

### 4. **Monitoring & Logging**
- `app/portfolio/settings_production.py`: Enhanced logging configuration
- Log levels for: django.request, django.db.backends, apps.comments

---

## Support & Resources

- **Neon Documentation**: https://neon.tech/docs/introduction
- **Django + PostgreSQL**: https://docs.djangoproject.com/en/4.2/ref/databases/#postgresql-notes
- **Cloud Run Secrets**: https://cloud.google.com/run/docs/configuring/secrets

For issues, check:
1. Cloud Run logs: `gcloud run services logs read blog-website`
2. Neon console: https://console.neon.tech
3. Django admin: Look for orphaned comment warnings

---

**Migration completed!** Your blog now runs on robust, persistent PostgreSQL infrastructure. 🎉
