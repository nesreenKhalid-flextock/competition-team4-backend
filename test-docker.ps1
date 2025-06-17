# Local Docker Testing Script (PowerShell)

Write-Host "Building Docker image locally..." -ForegroundColor Green
docker build -t group-ordering-app-local .

Write-Host "Running container locally on port 8080..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the container" -ForegroundColor Yellow
Write-Host "Test the API at: http://localhost:8080/api/health/" -ForegroundColor Cyan

docker run -p 8080:8080 --env PORT=8080 --env DEBUG=True group-ordering-app-local
