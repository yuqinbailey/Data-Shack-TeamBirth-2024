#!/bin/bash

# exit immediately if a command exits with a non-zero status
set -e

# Define some environment variables
export IMAGE_NAME="teambirth-llm-server"
export BASE_DIR=$(pwd)
export SECRETS_DIR=$(pwd)/../../../secrets/ 

# GCP artifact registry
docker build -t $IMAGE_NAME --platform=linux/amd64 -f Dockerfile .

# Run Container
docker run --rm --name $IMAGE_NAME -ti \
-v "$BASE_DIR":/app \
-v "$SECRETS_DIR":/secrets \
$IMAGE_NAME