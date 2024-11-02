# Frontend Dockerfile

# Use an appropriate base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Ensure necessary folders exist
RUN mkdir -p /app/uploads /app/temporary_uploads /app/analyze

RUN pip install --no-cache-dir tensorflow  # only CPU version

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire Frontend directory
COPY . .

# Expose the appropriate port (if necessary)
EXPOSE 5000

# Command to run your application
CMD ["python", "app.py"]

# Suppress TensorFlow logging
ENV TF_CPP_MIN_LOG_LEVEL=2
