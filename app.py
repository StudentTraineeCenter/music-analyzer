import os
import time
import threading
from flask import Flask, request, jsonify, render_template, url_for, send_from_directory, redirect, make_response
import librosa
import numpy as np
import subprocess
import time
import signal
import sys


app = Flask(__name__)
app.secret_key = 'your_secret_key'

progress = 0  # Global variable for tracking progress
audio_file_url = None  # Global variable for audio file URL
tempo = None  # Global variable for tempo

# Directories for uploads
UPLOADS_FOLDER = 'uploads'
TEMPORARY_UPLOADS_FOLDER = 'temporary_uploads'

# Ensure directories exist
os.makedirs(UPLOADS_FOLDER, exist_ok=True)
os.makedirs(TEMPORARY_UPLOADS_FOLDER, exist_ok=True)

@app.after_request
def add_header(response):
    # Prevent caching
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def index():
    # Render homepage
    return render_template('index.html')

@app.route('/progress')
def get_progress():
    global progress
    # Return current progress
    return jsonify({'progress': progress})

def is_file_free(filepath):
    # Check if file is ready to use
    for _ in range(20):
        try:
            with open(filepath, 'a'):
                return True
        except IOError:
            time.sleep(0.5)
    return False

def rename_file_if_needed(source_path, target_path):
    # Rename file if needed
    if os.path.exists(target_path):
        os.remove(target_path)
    try:
        os.rename(source_path, target_path)
    except Exception as e:
        print(f"Error renaming {source_path} to {target_path}: {e}")

def analyze_file(file_path, demucs_model):
    # Perform analysis
    global progress, audio_file_url, tempo
    try:
        progress = 20  # Begin analysis
        y, sr = librosa.load(file_path, sr=None)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        tempo = round(float(tempo) if not isinstance(tempo, np.ndarray) else tempo.item(), 2)
        progress = 40  # Audio file loaded successfully

        subprocess.run(['demucs', '-n', demucs_model, file_path], check=True)
        progress = 70  # Demucs finished processing

        time.sleep(2)  # Wait to ensure demucs has finished
        # Move separated files to temporary folder
        separated_folder = os.path.join('separated', demucs_model, os.path.splitext(os.path.basename(file_path))[0])
        if os.path.exists(separated_folder):
            rename_file_if_needed(os.path.join(separated_folder, 'vocals.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'vocals.wav'))
            rename_file_if_needed(os.path.join(separated_folder, 'guitar.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'guitar.wav'))
            rename_file_if_needed(os.path.join(separated_folder, 'bass.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'bass.wav'))
            rename_file_if_needed(os.path.join(separated_folder, 'piano.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'piano.wav'))
            rename_file_if_needed(os.path.join(separated_folder, 'drums.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'drums.wav'))
            rename_file_if_needed(os.path.join(separated_folder, 'other.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'other.wav'))

        progress = 90  # Files successfully renamed

        # creation of mixed_output.mp3
        output_file_path = os.path.join(TEMPORARY_UPLOADS_FOLDER, 'mixed_output.mp3')
        merge_command = [
            'ffmpeg',
            '-y',
            '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'vocals.wav'),
            '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'guitar.wav'),
            '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'bass.wav'),
            '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'piano.wav'),
            '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'drums.wav'),
            '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'other.wav'),
            '-filter_complex',
            '[0:a]volume=1.0,aformat=channel_layouts=stereo[v0];'
            '[1:a]volume=1.0,aformat=channel_layouts=stereo[v1];'
            '[2:a]volume=1.0,aformat=channel_layouts=stereo[v2];'
            '[3:a]volume=1.0,aformat=channel_layouts=stereo[v3];'
            '[4:a]volume=1.0,aformat=channel_layouts=stereo[v4];'
            '[5:a]volume=1.0,aformat=channel_layouts=stereo[v5];'
            '[v0][v1][v2][v3][v4][v5]amerge=inputs=6,aformat=channel_layouts=stereo',
            '-ac', '2',
            output_file_path
        ]

        try:
            subprocess.run(merge_command, check=True)
            progress = 100  # Analysis complete
            audio_file_url = 'mixed_output.mp3'  # Set the mixed output as the audio URL
        except subprocess.CalledProcessError as e:
            print(f"Error merging audio files: {e}")
            progress = 0

    except Exception as e:
        print(f"Error during analysis: {e}")
        progress = 0


@app.route('/analyze', methods=['POST'])
def analyze():
     # Start file analysis
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
    current_time = time.time()  # Get time
    audio_file_url = f"/temporary_uploads/mixed_output.mp3?cache_bust={current_time}"  # Add cache busting
    return render_template('results.html', audio_file_url=audio_file_url, tempo=tempo)

@app.route('/temporary_uploads/<filename>')
def serve_temp_file(filename):
    return send_from_directory(TEMPORARY_UPLOADS_FOLDER, filename)

UPLOADS_FOLDER = 'uploads'
TEMPORARY_UPLOADS_FOLDER = 'temporary_uploads'

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    try:
        # Clear temporary folders
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
    volume_settings = request.json  # Ensure this is a dictionary with required keys
    output_file_path = os.path.join(TEMPORARY_UPLOADS_FOLDER, 'mixed_output.mp3')
    
    # Create the mix command with formatted volumes
    mix_command = [
        'ffmpeg',
        '-y', 
        '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'vocals.wav'),
        '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'guitar.wav'),
        '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'bass.wav'),
        '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'piano.wav'),
        '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'drums.wav'),
        '-i', os.path.join(TEMPORARY_UPLOADS_FOLDER, 'other.wav'),
        '-filter_complex', (
            f"[0:a]volume={volume_settings['voice']},aformat=channel_layouts=stereo[v0];"
            f"[1:a]volume={volume_settings['guitar']},aformat=channel_layouts=stereo[v1];"
            f"[2:a]volume={volume_settings['bass']},aformat=channel_layouts=stereo[v2];"
            f"[3:a]volume={volume_settings['piano']},aformat=channel_layouts=stereo[v3];"
            f"[4:a]volume={volume_settings['drums']},aformat=channel_layouts=stereo[v4];"
            f"[5:a]volume={volume_settings['other']},aformat=channel_layouts=stereo[v5];"
            "[v0][v1][v2][v3][v4][v5]amerge=inputs=6[aout]"
        ),
        '-map', '[aout]', 
        '-ac', '2', 
        '-c:a', 'libmp3lame', 
        '-b:a', '192k', 
        output_file_path
    ]

    try:
        subprocess.run(mix_command, check=True)
        return jsonify({'audio_url': url_for('serve_temp_file', filename='mixed_output.mp3', _external=True)})
    except subprocess.CalledProcessError as e:
        print(f"Error mixing audio files: {e}")
        return jsonify({'error': 'Error mixing audio'}), 500
def cleanup_folders():
    for folder in [UPLOADS_FOLDER, TEMPORARY_UPLOADS_FOLDER]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
    print("Cleaned up folders.")

def signal_handler(sig, frame):
    print(f"Stopping the application due to signal: {sig}...")
    cleanup_folders()
    sys.exit(0)

if __name__ == "__main__":
    # Handle Ctrl+C and other termination signals
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    app.run(debug=True)