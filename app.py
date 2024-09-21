import os
import shutil
from flask import Flask, request, jsonify, render_template, url_for, send_from_directory
import librosa
import numpy as np
import yt_dlp
import subprocess

app = Flask(__name__)

UPLOADS_FOLDER = 'uploads'
TEMPORARY_UPLOADS_FOLDER = 'temporary_uploads'

# Ensure the folders exist
os.makedirs(UPLOADS_FOLDER, exist_ok=True)
os.makedirs(TEMPORARY_UPLOADS_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files.get('file')
    youtube_link = request.form.get('youtubeLink')
    demucs_model = request.form.get('demucsModel', 'mdx_extra')

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
            # Ensure tempo is a float
            tempo = float(tempo)

            # Use Demucs to separate instruments
            subprocess.run(['demucs', '-n', demucs_model, file_path], check=True)

            # Move the separated files to the temporary folder
            separated_folder = os.path.join('separated', demucs_model, os.path.splitext(os.path.basename(file_path))[0])
            if os.path.exists(separated_folder):
                for f in os.listdir(separated_folder):
                    shutil.move(os.path.join(separated_folder, f), os.path.join(TEMPORARY_UPLOADS_FOLDER, f))

            # Return URLs for the separated files and tempo
            instruments = [f for f in os.listdir(TEMPORARY_UPLOADS_FOLDER)]
            audio_url = url_for('serve_temp_file', filename=instruments[0])

            return jsonify({
                'tempo': tempo,
                'redirect_url': url_for('results', instruments=','.join(instruments), audio_file_url=os.path.basename(instruments[0]), tempo=tempo)
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'No file or link provided.'}), 400

@app.route('/results')
def results():
    instruments = request.args.get('instruments').split(',')
    audio_file_url = url_for('serve_temp_file', filename=request.args.get('audio_file_url'))
    tempo = request.args.get('tempo')  # Get tempo for display
    return render_template('results.html', instruments=instruments, audio_file_url=audio_file_url, tempo=tempo)

@app.route('/cleanup')
def cleanup():
    for filename in os.listdir(TEMPORARY_UPLOADS_FOLDER):
        file_path = os.path.join(TEMPORARY_UPLOADS_FOLDER, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    return 'Cleanup done'

@app.route('/temporary_uploads/<filename>')
def serve_temp_file(filename):
    return send_from_directory(TEMPORARY_UPLOADS_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
