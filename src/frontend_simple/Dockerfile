# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install the spaCy English model
RUN pip install spacy && \
    python -m spacy download en_core_web_sm

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=app.py
# ENV FLASK_RUN_HOST=0.0.0.0
ENV DATA_DIR=/data

# Run app.py when the container launches
# CMD ["flask", "run"]
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]