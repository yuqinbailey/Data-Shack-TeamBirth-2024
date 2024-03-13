#!/bin/bash

# exit immediately if a command exits with a non-zero status
set -e

# Define some environment variables
export IMAGE_NAME="teambirth-data-retrieval"
export BASE_DIR=$(pwd)
export SECRETS_DIR=$(pwd)/../secrets/ # make sure it matches your directory of secrets
export GCS_BUCKET_URI="gs://team-birth-2024"
export GCP_PROJECT="team-birth-2024"

# Build the image based on the Dockerfile
# docker build -t $IMAGE_NAME -f Dockerfile .
# M1/2 chip macs use this line
docker build -t $IMAGE_NAME --platform=linux/arm64/v8 -f Dockerfile .

# Run Container
docker run --rm --name $IMAGE_NAME -ti \
-v "$BASE_DIR":/app \
-v "$SECRETS_DIR":/secrets \
-e GOOGLE_APPLICATION_CREDENTIALS=/secrets/data-server-account.json \
-e GCP_PROJECT=$GCP_PROJECT \
-e GCS_BUCKET_URI=$GCS_BUCKET_URI \
$IMAGE_NAME
