# Frontend Dockerfile

# Use an appropriate base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

RUN pip install --no-cache-dir tensorflow  # only CPU version
# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire Frontend directory
COPY . .

# Expose the appropriate port (if necessary)
EXPOSE 3000

# Command to run your application
CMD ["python", "app.py"]

ENV TF_CPP_MIN_LOG_LEVEL=2
