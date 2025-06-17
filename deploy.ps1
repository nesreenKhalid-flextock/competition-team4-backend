# Google Cloud Run Deployment Script (PowerShell)
# Make sure you have gcloud CLI installed and authenticated

# Set your project variables
$PROJECT_ID = "flexdevelopment"
$SERVICE_NAME = "group-ordering-app"
$REGION = "us-central1"
$IMAGE_NAME = "us-central1-docker.pkg.dev/flexdevelopment/flex-development-docker-images/group-ordering-app"

Write-Host "Building and deploying to Google Cloud Run..." -ForegroundColor Green

# Build the Docker image
Write-Host "Building Docker image..." -ForegroundColor Yellow
docker build -t $IMAGE_NAME .

# Push to Google Container Registry
Write-Host "Pushing image to Google Container Registry..." -ForegroundColor Yellow
docker push $IMAGE_NAME

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --set-env-vars="DEBUG=False,SECRET_KEY=django-insecure-production-key-change-this,ALLOWED_HOSTS=*" `
    --memory=1Gi `
    --cpu=1 `
    --max-instances=10 `
    --port=8080 `
    --timeout=300 `
    --project $PROJECT_ID

Write-Host "Deployment completed!" -ForegroundColor Green
Write-Host "Your service URL:" -ForegroundColor Cyan
gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)" --project=$PROJECT_ID
