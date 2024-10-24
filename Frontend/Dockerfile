# Frontend/Dockerfile
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py .

# Copy static and templates directories
COPY static ./static
COPY Templates ./Templates

# Command to run the application
CMD ["python", "app.py"]
