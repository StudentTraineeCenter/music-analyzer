# Backend Dockerfile

# Use an appropriate base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app
COPY . /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire Backend directory
COPY . .

# Expose the appropriate port (if necessary)
EXPOSE 5000

# Command to run your application
CMD ["python", "audio_processor.py"]

ENV CUDA_VISIBLE_DEVICES=""
ENV TF_CPP_MIN_LOG_LEVEL=2

