#!/bin/bash

# exit immediately if a command exits with a non-zero status
set -e
set -x

# Define some environment variables
export IMAGE_NAME="tb24-api-service"
export BASE_DIR=$(pwd)
export SECRETS_DIR=$(pwd)/../../secrets/
export PERSISTENT_DIR=$(pwd)/../../persistent-folder/

# Build the image based on the Dockerfile
# docker build -t $IMAGE_NAME -f Dockerfile .

# M1/2 chip macs use this line
docker build -t $IMAGE_NAME --platform=linux/amd64 -f Dockerfile .