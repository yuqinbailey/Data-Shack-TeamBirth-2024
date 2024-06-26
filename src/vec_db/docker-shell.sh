#!/bin/bash

set -e

# Create the network if we don't have it yet
docker network inspect vec-db-network >/dev/null 2>&1 || docker network create vec-db-network

# Build the image based on the Dockerfile
docker build -t vec-db --platform=linux/arm64 -f Dockerfile .

# Ensure volume for persistent storage exists
# docker volume inspect metadata >/dev/null 2>&1 || docker volume create metadata

# Run the container with the volume
# docker run -d --name vec-db-container --network vec-db-network -v metadata:/app/metadata vec-db
docker-compose run --rm --service-ports vec-db