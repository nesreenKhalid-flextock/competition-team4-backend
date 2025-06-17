# Quick Deploy with Error Handling
param(
    [string]$ProjectId = "flexdevelopment"
)

$ServiceName = "group-ordering-app"
$Region = "us-central1"
$ImageName = "gcr.io/$ProjectId/$ServiceName"

try {
    Write-Host "=== Quick Deploy with Diagnostics ===" -ForegroundColor Cyan
    
    # Set project
    gcloud config set project $ProjectId
    
    # Build
    Write-Host "Building image..." -ForegroundColor Yellow
    docker build -t $ImageName . --no-cache
    if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }
    
    # Push
    Write-Host "Pushing image..." -ForegroundColor Yellow
    docker push $ImageName
    if ($LASTEXITCODE -ne 0) { throw "Docker push failed" }
    
    # Deploy with minimal config for testing
    Write-Host "Deploying with minimal config..." -ForegroundColor Yellow
    gcloud run deploy $ServiceName `
        --image $ImageName `
        --platform managed `
        --region $Region `
        --allow-unauthenticated `
        --memory=1Gi `
        --cpu=1 `
        --timeout=300 `
        --port=8080 `
        --set-env-vars="DEBUG=True,ALLOWED_HOSTS=*" `
        --project=$ProjectId
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Deployment successful!" -ForegroundColor Green
        $url = gcloud run services describe $ServiceName --region=$Region --format="value(status.url)" --project=$ProjectId
        Write-Host "Service URL: $url" -ForegroundColor Cyan
        Write-Host "Health check: $url/api/health/" -ForegroundColor Cyan
    } else {
        throw "Deployment failed"
    }
    
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Running diagnostics..." -ForegroundColor Yellow
    
    # Show recent logs
    gcloud logging read "resource.type=cloud_run_revision" --limit 5 --format="table(timestamp,severity,textPayload)" --project=$ProjectId
}
