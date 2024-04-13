# Use a Python 3.9 base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Define the command to run when the container starts
ENTRYPOINT ["python", "/app/generate_embeddings.py", "--name"]
CMD ["data_wa"]
