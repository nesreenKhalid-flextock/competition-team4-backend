#!/bin/bash

# Google Cloud Run Deployment Script
# Make sure you have gcloud CLI installed and authenticated

# Set your project variables
PROJECT_ID="your-project-id"
SERVICE_NAME="group-ordering-app"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "Building and deploying to Google Cloud Run..."

# Build the Docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

# Push to Google Container Registry
echo "Pushing image to Google Container Registry..."
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="DEBUG=False" \
  --memory=512Mi \
  --cpu=1 \
  --max-instances=10 \
  --port=8080

echo "Deployment completed!"
echo "Your service URL:"
gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"
