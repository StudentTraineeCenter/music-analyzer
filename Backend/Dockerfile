# Backend Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the backend source code
COPY . .

# Expose the backend port (adjust if needed)
EXPOSE 5000

# Command to run the backend
CMD ["python", "audio_processor.py"]
