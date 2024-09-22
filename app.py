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
progress = 0  # Global variable for tracking progress

# Ensure the folders exist
os.makedirs(UPLOADS_FOLDER, exist_ok=True)
os.makedirs(TEMPORARY_UPLOADS_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/progress')
def get_progress():
    return jsonify({'progress': progress})

def is_file_free(filepath):
    try:
        with open(filepath, 'a'):
            pass
        return True
    except IOError:
        return False

def safe_rename(src, dest):
    for _ in range(10):
        if is_file_free(src):
            try:
                os.rename(src, dest)
                return True
            except OSError as e:
                print(f"Error renaming {src} to {dest}: {e}")
        time.sleep(1)
    print(f"Failed to rename {src} to {dest} after multiple attempts.")
    return False

@app.route('/analyze', methods=['POST'])
def analyze():
    global progress
    progress = 0

    file = request.files.get('file')
    youtube_link = request.form.get('youtubeLink')
    demucs_model = request.form.get('demucsModel', 'htdemucs_6s')

    file_path = None
    if file:
        filename = file.filename
        file_path = os.path.join(UPLOADS_FOLDER, filename)
        file.save(file_path)
        progress = 10  # Update progress
    elif youtube_link:
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(UPLOADS_FOLDER, '%(id)s.%(ext)s'),
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_link, download=True)
                file_path = os.path.join(UPLOADS_FOLDER, f"{info_dict['id']}.mp3")
            progress = 30  # Update progress
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    if file_path:
        try:
            y, sr = librosa.load(file_path, sr=None)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            tempo = float(tempo) if not isinstance(tempo, np.ndarray) else tempo.item()

            subprocess.run(['demucs', '-n', demucs_model, file_path], check=True)
            progress = 70  # Update progress

            time.sleep(2)

            separated_folder = os.path.join('separated', demucs_model, os.path.splitext(os.path.basename(file_path))[0])
            if os.path.exists(separated_folder):
                for f in os.listdir(separated_folder):
                    src_path = os.path.join(separated_folder, f)
                    dest_path = os.path.join(TEMPORARY_UPLOADS_FOLDER, f)
                    safe_rename(src_path, dest_path)
            progress = 90  # Update progress

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
                '-ac', '2',
                output_file_path
            ]
            subprocess.run(merge_command, check=True)
            progress = 100  # Update progress

            audio_url = url_for('serve_temp_file', filename='final_output.mp3')
            session['audio_file_url'] = 'final_output.mp3'
            session['tempo'] = tempo

            return jsonify({'redirect_url': url_for('results')})
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
    for folder in [UPLOADS_FOLDER, TEMPORARY_UPLOADS_FOLDER]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
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
