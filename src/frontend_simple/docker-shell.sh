#!/bin/bash

# exit immediately if a command exits with a non-zero status
set -e

export IMAGE_NAME="frontend-simple"
export BASE_DIR=$(pwd)

# Build the image based on the Dockerfile
docker build -t $IMAGE_NAME -f Dockerfile .

# Run the container
# --v: Attach a filesystem volume to the container
# -p: Publish a container's port(s) to the host (host_port: container_port) (source: https://dockerlabs.collabnix.com/intermediate/networking/ExposingContainerPort.html)
docker run --rm --name $IMAGE_NAME -d \
-p 5001:5000 $IMAGE_NAME
