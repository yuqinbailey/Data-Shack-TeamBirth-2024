#FROM python:3.8-slim
# bitsandbytes requires CUDA
FROM nvidia/cuda:11.3.1-base-ubuntu20.04

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required dependencies
COPY requirements.txt .
RUN apt update && apt install -y python pip && pip install --no-cache-dir -r requirements.txt

# Specify the command to run on container start
CMD ["uvicorn", "llm_service:app", "--host", "0.0.0.0", "--port", "8000"]

