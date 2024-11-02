from flask import Flask, request, jsonify, render_template, url_for, send_from_directory, redirect
import os
import sys
import time
import requests  # Import requests for making API calls to backend

app = Flask(__name__, template_folder='templates', static_folder='static')
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

    if file:
        temp_file_path = os.path.join(UPLOADS_FOLDER, file.filename)
        file.save(temp_file_path)
        progress = 10  # Update progress after file is saved

        # Send POST request to the backend for analysis
        backend_response = requests.post(
            "http://backend:5001/analyze", 
            files={'file': open(temp_file_path, 'rb')}, 
            data={'demucsModel': demucs_model}
        )

        if backend_response.status_code == 202:
            return jsonify({'message': 'Analysis started'}), 202
        else:
            return jsonify({'error': 'Analysis failed'}), 500

    return jsonify({'error': 'No file provided.'}), 400

@app.route('/results')
def results():
    global audio_file_url, tempo
    if not audio_file_url or tempo is None:
        return redirect(url_for('index'))  # Redirect back if no results
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
