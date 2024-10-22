FROM python:3.9-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libatlas-base-dev \
    && pip install --no-cache-dir numpy==1.21.0 \
    && pip install --no-cache-dir spleeter

# Set your working directory
WORKDIR /app

# Copy your requirements file
COPY requirements.txt .

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application files
COPY . .

# Command to run your app
CMD ["python", "app.py"]
