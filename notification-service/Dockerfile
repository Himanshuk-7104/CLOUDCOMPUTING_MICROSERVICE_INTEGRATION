# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the application dependencies requirements file to the container
COPY requirements.txt .

# Install any dependencies
RUN pip install -r requirements.txt

# Copy the application code to the container
COPY . .

# Expose the port that the Flask application runs on
EXPOSE 5000

# Define the command to run the application
CMD ["python", "app.py"]