# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . .

# Command to run the application
# This tells the container to execute the uvicorn server
# It will bind to all network interfaces (0.0.0.0) and use the port
# provided by the Cloud Run environment variable ($PORT, typically 8080)
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT    