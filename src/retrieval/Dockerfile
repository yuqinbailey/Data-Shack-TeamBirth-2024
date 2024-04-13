# Use the official Debian-hosted Python image
FROM python:3.9-slim-buster
# FROM python:3.9-slim

ARG DEBIAN_PACKAGES="build-essential git curl wget unzip gzip"

# Prevent apt from showing prompts
ENV DEBIAN_FRONTEND=noninteractive

# Python wants UTF-8 locale
ENV LANG=C.UTF-8

# Tell pipenv where the shell is. 
# This allows us to use "pipenv shell" as a container entry point.
ENV PYENV_SHELL=/bin/bash

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Define the command to run when the container starts
ENTRYPOINT ["/bin/bash","./entrypoint.sh"]
