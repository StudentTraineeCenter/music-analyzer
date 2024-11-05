FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

#RUN pip install --no-cache-dir tensorflow  # only CPU version
COPY . .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
# EXPOSE 5000

# # Command to run your application
# CMD ["python", "app.py"]

# # Suppress TensorFlow logging
# ENV TF_CPP_MIN_LOG_LEVEL=2