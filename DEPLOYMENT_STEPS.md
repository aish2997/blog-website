# Deployment Steps: Neon PostgreSQL Integration

## ✅ Completed Configuration

### Local Development
- ✅ Fixed `.env` file to use `portfolio.settings` (development settings)
- ✅ Configured to use SQLite locally (simple and fast)
- ✅ Removed conflicting production settings
- ✅ Server now starts successfully at http://127.0.0.1:8000/

### Terraform Updates
- ✅ Added `neon-database-url` secret definition in `terraform/infrastructure/secrets.tf`
- ✅ Updated Cloud Run configuration in `terraform/infrastructure/main.tf`:
  - Added `DATABASE_URL` environment variable from Secret Manager
  - Removed `DATABASE_PATH` environment variable (no more ephemeral SQLite)
- ✅ Created helper script: `scripts/add-neon-secret.sh`

---

## 🚀 Deployment Process

### Step 1: Apply Terraform Configuration

This will create the secret container in Google Secret Manager and update Cloud Run configuration.

```bash
cd terraform/infrastructure
terraform init
terraform plan  # Review the changes
terraform apply  # Apply the changes
```

**Expected changes:**
- Create `neon-database-url` secret in Secret Manager
- Create IAM binding for Cloud Run to access the secret
- Update Cloud Run service to use `DATABASE_URL` instead of `DATABASE_PATH`

### Step 2: Add Secret Value to Google Secret Manager

After Terraform creates the secret container, add the actual Neon connection string:

**Option A: Using the helper script (recommended)**
```bash
cd /Users/aishwaryabhargava/blog-website
./scripts/add-neon-secret.sh
```

**Option B: Using gcloud CLI directly**
```bash
echo -n "postgresql://neondb_owner:npg_aE1htmuSIPA4@ep-falling-fire-agw51vny-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require" | \
  gcloud secrets versions add neon-database-url --data-file=-
```

**Option C: Using GCP Console**
1. Go to GCP Console → Security → Secret Manager
2. Find the `neon-database-url` secret
3. Click "NEW VERSION"
4. Paste: `postgresql://neondb_owner:npg_aE1htmuSIPA4@ep-falling-fire-agw51vny-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require`
5. Click "ADD SECRET VERSION"

### Step 3: Deploy to Cloud Run

**Option A: Using GitHub Actions (automatic)**
```bash
git add .
git commit -m "Configure Neon PostgreSQL for production"
git push origin main  # or your production branch
```

This will trigger the GitHub Actions workflow defined in `.github/workflows/deploy.yaml`

**Option B: Manual deployment**
```bash
cd terraform/infrastructure
terraform apply  # This will update the Cloud Run service with new environment variables
```

### Step 4: Verify Production Database

After deployment completes, verify that Cloud Run is using PostgreSQL:

```bash
# View Cloud Run logs
gcloud run services logs tail [your-service-name] --region=[your-region]
```

Look for:
- ✅ `"✅ Using PostgreSQL from DATABASE_URL"`
- ✅ No errors about database connections
- ✅ Migrations running successfully

**Test the production site:**
1. Open your Cloud Run URL in a browser
2. Log into the admin panel
3. Create a test blog post
4. Redeploy the service (or restart it)
5. Verify the blog post still exists (data persists!)

---

## 📋 Summary of Changes

### Files Modified:

1. **`app/.env`** - Fixed for local development
   - Removed `DJANGO_SETTINGS_MODULE=portfolio.settings_production`
   - Removed `DATABASE_URL` (uses SQLite locally)
   - Now uses development settings by default

2. **`terraform/infrastructure/secrets.tf`** - Added Neon secret
   - Added `neon_database_url` secret resource
   - Added IAM binding for Cloud Run access
   - Updated output instructions

3. **`terraform/infrastructure/main.tf`** - Updated Cloud Run config
   - Added `DATABASE_URL` env var from Secret Manager
   - Removed `DATABASE_PATH` env var

4. **`scripts/add-neon-secret.sh`** - Helper script (new)
   - Automates adding the secret value to GCP

5. **`app/portfolio/settings_production.py`** - Already configured
   - Supports `DATABASE_URL` environment variable
   - Falls back to SQLite if not provided
   - Uses `dj-database-url` for parsing

---

## 🎯 Architecture Summary

### Local Development
```
Developer Machine
├── Settings: portfolio.settings
├── Database: SQLite (db.sqlite3)
├── DEBUG: True
└── Access: http://127.0.0.1:8000/
```

### Production (Cloud Run)
```
Cloud Run Service
├── Settings: portfolio.settings_production
├── Database: Neon PostgreSQL (production branch)
├── DATABASE_URL: From Secret Manager
├── DEBUG: False
└── Access: https://your-app.run.app
```

### Benefits of This Setup:
- ✅ **Local dev is fast**: SQLite, no network dependency
- ✅ **Production is persistent**: Neon PostgreSQL, data survives deployments
- ✅ **Dev/prod separation**: Local changes don't affect production
- ✅ **Secure**: Database credentials stored in Secret Manager
- ✅ **Scalable**: Neon auto-scales with your application

---

## 🔍 Troubleshooting

### Local server won't start
```bash
cd /Users/aishwaryabhargava/blog-website/app
python manage.py check
```

If issues persist, verify `.env` file has NO `DJANGO_SETTINGS_MODULE` or `DATABASE_URL` set.

### Production not using PostgreSQL
Check Cloud Run environment variables:
```bash
gcloud run services describe [service-name] --region=[region] --format="value(spec.template.spec.containers[0].env)"
```

Verify `DATABASE_URL` is present and references the secret.

### Secret not found
Verify the secret exists:
```bash
gcloud secrets list | grep neon-database-url
```

If missing, run `terraform apply` again.

### Database connection errors
Check the Neon connection string in Secret Manager:
```bash
gcloud secrets versions access latest --secret=neon-database-url
```

Verify it matches your Neon console connection string.

---

## ✨ Next Steps (Optional)

### 1. Use Neon Dev Branch Locally (Optional)
If you want to use Neon's development branch instead of SQLite:

1. Get your Neon dev branch connection string from Neon Console
2. Modify `app/portfolio/settings.py` to support `DATABASE_URL`
3. Add `DATABASE_URL=postgresql://...dev-branch...` to `.env`

### 2. Configure Google OAuth (For Comments)
Once production is stable:
1. Follow `GOOGLE_OAUTH_SETUP.md`
2. Set up OAuth in Google Cloud Console
3. Configure in Django admin
4. Test comment authentication

### 3. Monitor Database Performance
- Use Neon Console to monitor query performance
- Set up alerts for connection issues
- Review slow queries

---

## 📚 Related Documentation

- `MIGRATION_TO_POSTGRESQL.md` - Original migration guide
- `GOOGLE_OAUTH_SETUP.md` - OAuth configuration guide
- `IMPLEMENTATION_STATUS.md` - Overall project status
- `terraform/infrastructure/README.md` - Terraform documentation

---

## 🎉 Success Criteria

Your deployment is successful when:
- ✅ Local server runs at http://127.0.0.1:8000/
- ✅ Production deploys without errors
- ✅ Cloud Run logs show PostgreSQL connection
- ✅ Data persists across deployments
- ✅ Admin panel works in production
- ✅ No database connection errors in logs
