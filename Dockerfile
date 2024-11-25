FROM python:3.9-slim

WORKDIR /app
COPY prepare.py prepare.py
RUN python3 prepare.py
RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean
RUN python3 -m pip install -U demucs
COPY . .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
# EXPOSE 5000

# # Command to run your application
# CMD ["python", "app.py"]

# # Suppress TensorFlow logging
# ENV TF_CPP_MIN_LOG_LEVEL=2