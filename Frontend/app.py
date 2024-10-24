from flask import Flask, request, jsonify, render_template, url_for, send_from_directory, redirect
import os
import sys
import time
import threading
import subprocess
from Backend.audio_processor import analyze_file  # Adjust based on what you need
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
app = Flask(__name__, template_folder='../Frontend/templates', static_folder='../Frontend/static')
app.secret_key = 'your_secret_key'

UPLOADS_FOLDER = 'uploads'
TEMPORARY_UPLOADS_FOLDER = 'temporary_uploads'
progress = 0  # Global variable for tracking progress
audio_file_url = None  # Global variable for audio file URL
tempo = None  # Global variable for tempo

# Ensure the folders exist
os.makedirs(UPLOADS_FOLDER, exist_ok=True)
os.makedirs(TEMPORARY_UPLOADS_FOLDER, exist_ok=True)

@app.after_request
def add_header(response):
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/progress')
def get_progress():
    global progress
    return jsonify({'progress': progress})

@app.route('/analyze', methods=['POST'])
def analyze():
    global progress
    progress = 0

    file = request.files.get('file')
    demucs_model = request.form.get('demucsModel', 'htdemucs_6s')

    file_path = None
    if file:
        filename = file.filename
        file_path = os.path.join(UPLOADS_FOLDER, filename)
        file.save(file_path)
        progress = 10  # Update progress after file is saved

    if file_path:
        # Start analysis in a new thread
        analysis_thread = threading.Thread(target=analyze_file, args=(file_path, demucs_model))
        analysis_thread.start()

        # Return immediately to avoid blocking
        return jsonify({'message': 'Analysis started'}), 202

    return jsonify({'error': 'No file provided.'}), 400

@app.route('/results')
def results():
    global audio_file_url, tempo
    if not audio_file_url or tempo is None:
        return redirect(url_for('index'))  # Redirect back if no results
    current_time = time.time()  # Get current time
    audio_file_url = f"/temporary_uploads/mixed_output.mp3?cache_bust={current_time}"  # Add cache busting
    return render_template('results.html', audio_file_url=audio_file_url, tempo=tempo)

@app.route('/temporary_uploads/<filename>')
def serve_temp_file(filename):
    return send_from_directory(TEMPORARY_UPLOADS_FOLDER, filename)

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    try:
        # Remove files in the folders
        for folder in [UPLOADS_FOLDER, TEMPORARY_UPLOADS_FOLDER]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error cleaning up files: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/mix', methods=['POST'])
def mix():
    volume_settings = request.json
    output_file_path = os.path.join(TEMPORARY_UPLOADS_FOLDER, 'mixed_output.mp3')
    
    # Prepare ffmpeg command for mixing sound
    mix_command = [
        'ffmpeg',
        '-y', 
        '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'vocals.wav'),
        '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'guitar.wav'),
        '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'bass.wav'),
        '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'piano.wav'),
        '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'drums.wav'),
        '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'other.wav'),
        '-filter_complex', f"[0:a]volume={volume_settings['voice']}[v0];[1:a]volume={volume_settings['guitar']}[v1];[2:a]volume={volume_settings['bass']}[v2];[3:a]volume={volume_settings['piano']}[v3];[4:a]volume={volume_settings['drums']}[v4];[5:a]volume={volume_settings['other']}[v5];[v0][v1][v2][v3][v4][v5]amerge=inputs=6",
        '-ac', '2',
        output_file_path
    ]

    try:
        subprocess.run(mix_command, check=True)
        return jsonify({'audio_url': url_for('serve_temp_file', filename='mixed_output.mp3', _external=True)})
    except subprocess.CalledProcessError as e:
        print(f"Error mixing audio files: {e}")
        return jsonify({'error': 'Error mixing audio'}), 500

if __name__ == "__main__":
    app.run(debug=True)
