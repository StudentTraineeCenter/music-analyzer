import os
import shutil
import time
from flask import Flask, request, jsonify, render_template, url_for, send_from_directory, session
import librosa
import numpy as np
import yt_dlp
import subprocess
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

UPLOADS_FOLDER = 'uploads'
TEMPORARY_UPLOADS_FOLDER = 'temporary_uploads'

# Ensure the folders exist
os.makedirs(UPLOADS_FOLDER, exist_ok=True)
os.makedirs(TEMPORARY_UPLOADS_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

def is_file_free(filepath):
    """Check if a file can be accessed for writing."""
    try:
        with open(filepath, 'a'):
            pass
        return True
    except IOError:
        return False

def safe_rename(src, dest):
    """Safely rename a file with retries."""
    for _ in range(10):  # Try up to 10 times
        if is_file_free(src):
            try:
                os.rename(src, dest)
                return True
            except OSError as e:
                print(f"Error renaming {src} to {dest}: {e}")
        time.sleep(1)  # Wait 1 second before retrying
    print(f"Failed to rename {src} to {dest} after multiple attempts.")
    return False

@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files.get('file')
    youtube_link = request.form.get('youtubeLink')
    demucs_model = request.form.get('demucsModel', 'htdemucs_6s')  # Use the experimental 6 sources model

    file_path = None
    if file:
        filename = file.filename
        file_path = os.path.join(UPLOADS_FOLDER, filename)
        file.save(file_path)
    elif youtube_link:
        try:
            # Download audio using yt-dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(UPLOADS_FOLDER, '%(id)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_link, download=True)
                file_path = os.path.join(UPLOADS_FOLDER, f"{info_dict['id']}.mp3")
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    if file_path:
        try:
            # Analyze tempo using librosa
            y, sr = librosa.load(file_path, sr=None)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

            if isinstance(tempo, np.ndarray):
                tempo = tempo.item()
            tempo = float(tempo)

            # Use Demucs to separate instruments
            subprocess.run(['demucs', '-n', demucs_model, file_path], check=True)

            # Wait for file operations to settle
            time.sleep(2)

            # Move the separated files to the temporary folder
            separated_folder = os.path.join('separated', demucs_model, os.path.splitext(os.path.basename(file_path))[0])
            if os.path.exists(separated_folder):
                for f in os.listdir(separated_folder):
                    src_path = os.path.join(separated_folder, f)
                    dest_path = os.path.join(TEMPORARY_UPLOADS_FOLDER, f)
                    safe_rename(src_path, dest_path)

            # Sloučení stop do jedné
            output_file_path = os.path.join(TEMPORARY_UPLOADS_FOLDER, 'final_output.mp3')
            merge_command = [
                'ffmpeg',
                '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'vocals.wav'),
                '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'guitar.wav'),
                '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'bass.wav'),
                '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'piano.wav'),
                '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'drums.wav'),
                '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'other.wav'),
                '-filter_complex', 'amerge=inputs=6',
                '-c:a', 'libmp3lame',
                '-ac', '2',  # Stereo output
                output_file_path
            ]
            subprocess.run(merge_command, check=True)

            # Return URL for the merged file and tempo
            audio_url = url_for('serve_temp_file', filename='final_output.mp3')

            # Store instruments in session as JSON
            session['audio_file_url'] = 'final_output.mp3'
            session['tempo'] = tempo

            return jsonify({
                'redirect_url': url_for('results')
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'No file or link provided.'}), 400

@app.route('/results')
def results():
    audio_file_url = url_for('serve_temp_file', filename=session.get('audio_file_url'))
    tempo = session.get('tempo')
    return render_template('results.html', audio_file_url=audio_file_url, tempo=tempo)

@app.route('/cleanup', methods=['POST'])
def cleanup():
    # Remove files from uploads folder
    for filename in os.listdir(UPLOADS_FOLDER):
        file_path = os.path.join(UPLOADS_FOLDER, filename)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Error removing {file_path}: {e}")

    # Remove files from temporary uploads folder
    for filename in os.listdir(TEMPORARY_UPLOADS_FOLDER):
        file_path = os.path.join(TEMPORARY_UPLOADS_FOLDER, filename)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Error removing {file_path}: {e}")

    return 'Cleanup done'


@app.route('/temporary_uploads/<filename>')
def serve_temp_file(filename):
    return send_from_directory(TEMPORARY_UPLOADS_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
