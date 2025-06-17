# Group Ordering App - Deployment Guide

This Django REST API application is configured for deployment to Google Cloud Run using Docker and Gunicorn.

## Prerequisites

1. **Google Cloud CLI**: Install and authenticate with `gcloud auth login`
2. **Docker**: Install Docker on your local machine
3. **Google Cloud Project**: Create a project and enable the following APIs:
   - Cloud Run API
   - Cloud Build API
   - Container Registry API

## Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

```bash
# Required
SECRET_KEY=your-super-secret-key-here
DEBUG=False
DATABASE_URL=postgresql://user:password@host:port/database

# Optional
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
```

## Local Development

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run migrations:

```bash
python manage.py migrate
```

3. Create superuser:

```bash
python manage.py createsuperuser
```

4. Run development server:

```bash
python manage.py runserver
```

## Deployment Options

### Option 1: Using Cloud Build (Recommended)

1. Set your project ID:

```bash
gcloud config set project YOUR_PROJECT_ID
```

2. Submit build to Cloud Build:

```bash
gcloud builds submit --config cloudbuild.yaml
```

### Option 2: Manual Deployment

1. Build and push Docker image:

```bash
# Replace YOUR_PROJECT_ID with your actual project ID
docker build -t gcr.io/YOUR_PROJECT_ID/group-ordering-app .
docker push gcr.io/YOUR_PROJECT_ID/group-ordering-app
```

2. Deploy to Cloud Run:

```bash
gcloud run deploy group-ordering-app \
  --image gcr.io/YOUR_PROJECT_ID/group-ordering-app \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="DEBUG=False,SECRET_KEY=your-secret-key" \
  --memory=512Mi \
  --cpu=1
```

### Option 3: Using Deployment Scripts

For Linux/Mac:

```bash
chmod +x deploy.sh
./deploy.sh
```

For Windows PowerShell:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\deploy.ps1
```

## API Endpoints

Once deployed, your API will have the following endpoints:

### Health Check

- `GET /api/health/` - API health check

### Authentication

- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/token/refresh/` - Refresh JWT token
- `POST /api/auth/token/verify/` - Verify JWT token

### User Profile

- `GET /api/auth/profile/` - Get user profile
- `PUT /api/auth/profile/update/` - Update user profile
- `PUT /api/auth/change-password/` - Change password

## Configuration Details

### Gunicorn Configuration

The app uses `gunicorn.conf.py` for production-ready configuration:

- Auto-scaling workers based on CPU cores
- Request timeouts and keepalive settings
- Proper logging configuration
- SSL/HTTPS support

### Static Files

- Static files are served using WhiteNoise middleware
- Files are compressed and cached for better performance
- Media files can be served locally or via Google Cloud Storage

### Security Features

- HTTPS enforcement in production
- Secure cookies and headers
- CORS configuration for frontend integration
- JWT token authentication

## Database Migrations

Run migrations after deployment:

```bash
gcloud run services update group-ordering-app \
  --region us-central1 \
  --command="python,manage.py,migrate"
```

## Monitoring and Logs

View logs in Cloud Run:

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=group-ordering-app" --limit 50 --format "table(timestamp,textPayload)"
```

## Troubleshooting

### Common Issues

1. **Port Issues**: Make sure the PORT environment variable is set to 8080
2. **Database Connection**: Verify DATABASE_URL is correctly formatted
3. **Static Files**: Run `collectstatic` if static files aren't loading
4. **Memory Issues**: Increase memory allocation in Cloud Run if needed

### Useful Commands

```bash
# Check service status
gcloud run services describe group-ordering-app --region us-central1

# Update environment variables
gcloud run services update group-ordering-app \
  --region us-central1 \
  --set-env-vars="DEBUG=False,NEW_VAR=value"

# Scale service
gcloud run services update group-ordering-app \
  --region us-central1 \
  --memory=1Gi \
  --cpu=2
```

## Cost Optimization

- Cloud Run charges only for actual usage
- Consider setting max instances to control costs
- Use Cloud Build triggers for automatic deployments
- Monitor usage in Google Cloud Console
