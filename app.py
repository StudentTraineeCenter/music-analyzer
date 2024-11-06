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
import shutil

app = Flask(__name__)
app.secret_key = 'your_secret_key'

progress = 0  # Global variable for tracking progress
audio_file_url = None  # Global variable for audio file URL
tempo = None  # Global variable for tempo

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

def is_file_free(filepath):
    for _ in range(20):
        try:
            with open(filepath, 'a'):
                return True
        except IOError:
            time.sleep(0.5)
    return False

def rename_file_if_needed(source_path, target_path):
    if os.path.exists(target_path):
        os.remove(target_path)
    try:
        os.rename(source_path, target_path)
    except Exception as e:
        print(f"Error renaming {source_path} to {target_path}: {e}")

def analyze_file(file_path, demucs_model):
    global progress, audio_file_url, tempo
    try:
        progress = 20  # Begin analysis
        y, sr = librosa.load(file_path, sr=None)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        tempo = float(tempo) if not isinstance(tempo, np.ndarray) else tempo.item()
        progress = 40  # Audio file loaded successfully

        subprocess.run(['demucs', '-n', demucs_model, file_path], check=True)
        progress = 70  # Demucs finished processing

        time.sleep(2)  # Wait to ensure demucs has finished

        separated_folder = os.path.join('separated', demucs_model, os.path.splitext(os.path.basename(file_path))[0])
        if os.path.exists(separated_folder):
            rename_file_if_needed(os.path.join(separated_folder, 'vocals.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'vocals.wav'))
            rename_file_if_needed(os.path.join(separated_folder, 'guitar.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'guitar.wav'))
            rename_file_if_needed(os.path.join(separated_folder, 'bass.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'bass.wav'))
            rename_file_if_needed(os.path.join(separated_folder, 'piano.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'piano.wav'))
            rename_file_if_needed(os.path.join(separated_folder, 'drums.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'drums.wav'))
            rename_file_if_needed(os.path.join(separated_folder, 'other.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'other.wav'))

        progress = 90  # Files successfully renamed

        # Vytvoření mixed_output.mp3 se standardní hlasitostí
        output_file_path = os.path.join(TEMPORARY_UPLOADS_FOLDER, 'mixed_output.mp3')
        merge_command = [
            'ffmpeg',
            '-y',  # Overwrite existing files
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
    current_time = time.time()  # Získej aktuální čas
    audio_file_url = f"/temporary_uploads/mixed_output.mp3?cache_bust={current_time}"  # Přidej cache busting
    return render_template('results.html', audio_file_url=audio_file_url, tempo=tempo)

@app.route('/temporary_uploads/<filename>')
def serve_temp_file(filename):
    return send_from_directory(TEMPORARY_UPLOADS_FOLDER, filename)

UPLOADS_FOLDER = 'uploads'
TEMPORARY_UPLOADS_FOLDER = 'temporary_uploads'

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    try:
        # Odstranit soubory ve složkách
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
    
    # Připrav příkaz ffmpeg pro míchání zvuku
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