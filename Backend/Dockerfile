# Frontend Dockerfile

# Use the appropriate base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app directory
COPY . .

# Expose the appropriate port (if necessary)
EXPOSE 3000

# Command to run your application
CMD ["python", "app.py"]
