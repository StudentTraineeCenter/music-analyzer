import os

UPLOADS_FOLDER = 'uploads'
TEMPORARY_UPLOADS_FOLDER = 'temporary_uploads'


# Ensure the folders exist
os.makedirs(UPLOADS_FOLDER, exist_ok=True)
os.makedirs(TEMPORARY_UPLOADS_FOLDER, exist_ok=True)
