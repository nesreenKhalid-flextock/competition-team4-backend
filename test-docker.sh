#!/bin/bash

# Local Docker Testing Script

echo "Building Docker image locally..."
docker build -t group-ordering-app-local .

echo "Running container locally on port 8080..."
docker run -p 8080:8080 --env PORT=8080 --env DEBUG=True group-ordering-app-local

echo "Test the API at: http://localhost:8080/api/health/"
