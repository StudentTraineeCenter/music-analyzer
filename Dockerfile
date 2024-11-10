FROM python:3.9-slim


# RUN git clone --depth 1 --branch v4.0.1 --single-branch https://github.com/facebookresearch/demucs /lib/demucs
# WORKDIR /lib/demucs
# Install dependencies
# RUN python3 -m pip install -e . --no-cache-dir
# Run once to ensure demucs works and trigger the default model download
# RUN python3 -m demucs -d cpu test.mp3 
# Cleanup output - we just used this to download the model
# RUN rm -r separated

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt
RUN python3 -m pip install -U demucs

#RUN pip install --no-cache-dir tensorflow  # only CPU version
COPY prepare.py prepare.py
RUN python3 prepare.py

# RUN python3 -m pip install -U htdemucs

COPY . .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
# EXPOSE 5000

# # Command to run your application
# CMD ["python", "app.py"]

# # Suppress TensorFlow logging
# ENV TF_CPP_MIN_LOG_LEVEL=2