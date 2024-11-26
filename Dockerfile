FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

# Install Demucs
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -U demucs

# Copy the requirements and install Python dependencies
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose Flask port
EXPOSE 5000

# Command to run your application
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]

# Suppress TensorFlow logging
ENV TF_CPP_MIN_LOG_LEVEL=2
