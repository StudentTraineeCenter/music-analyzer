# Backend/Dockerfile
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY audio_processor.py .

# Command to run the application
CMD ["python", "audio_processor.py"]
