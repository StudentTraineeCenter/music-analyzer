
FROM python:3.9-slim

WORKDIR /app

# Install Spleeter and required dependencies
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean
RUN pip install --no-cache-dir spleeter
RUN python3 -m pip install -U demucs

COPY spleeter_service.py .

CMD ["python", "spleeter_service.py"]
