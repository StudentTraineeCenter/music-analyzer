import os
import time
import json
import subprocess
import librosa
import numpy as np
from http.server import SimpleHTTPRequestHandler
import socketserver
from spleeter.separator import Separator

TEMPORARY_UPLOADS_FOLDER = 'temporary_uploads'
progress = 0  # Global variable for tracking progress
audio_file_url = None  # Global variable for audio file URL
tempo = None  # Global variable for tempo

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

def analyze_file(file_path, demucs_model='htdemucs_6s'):
    global progress, audio_file_url, tempo
    try:
        progress = 20  # Begin analysis
        y, sr = librosa.load(file_path, sr=None)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        tempo = float(tempo) if not isinstance(tempo, np.ndarray) else tempo.item()
        progress = 40  # Audio file loaded successfully

        # Use Spleeter for all stems except guitar
        separator = Separator('spleeter:5stems')
        separator.separate_to_file(file_path, TEMPORARY_UPLOADS_FOLDER)
        spleeter_folder = os.path.join(TEMPORARY_UPLOADS_FOLDER, os.path.splitext(os.path.basename(file_path))[0])

        # Rename Spleeter output files
        rename_file_if_needed(os.path.join(spleeter_folder, 'vocals.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'vocals.wav'))
        rename_file_if_needed(os.path.join(spleeter_folder, 'bass.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'bass.wav'))
        rename_file_if_needed(os.path.join(spleeter_folder, 'piano.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'piano.wav'))
        rename_file_if_needed(os.path.join(spleeter_folder, 'drums.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'drums.wav'))
        rename_file_if_needed(os.path.join(spleeter_folder, 'other.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'other.wav'))

        progress = 60  # Spleeter separation completed

        # Use Demucs for guitar extraction
        subprocess.run(['demucs', '-n', demucs_model, file_path], check=True)
        demucs_folder = os.path.join('separated', demucs_model, os.path.splitext(os.path.basename(file_path))[0])
        if os.path.exists(demucs_folder):
            rename_file_if_needed(os.path.join(demucs_folder, 'guitar.wav'), os.path.join(TEMPORARY_UPLOADS_FOLDER, 'guitar.wav'))

        progress = 90  # Demucs finished processing

        # Create mixed_output.mp3 with standard volume
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
            audio_file_url = '/temporary_uploads/mixed_output.mp3'
        except subprocess.CalledProcessError as e:
            print(f"Error merging audio files: {e}")
    except Exception as e:
        print(f"Error during file analysis: {e}")
        progress = 100  # Analysis failed

class MusicAnalysisHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            file_path = data.get("file_path")
            demucs_model = data.get("demucs_model", 'htdemucs_6s')
            
            if file_path and os.path.exists(file_path):
                analyze_file(file_path, demucs_model)
                
                # Return JSON response
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                
                response = json.dumps({
                    "progress": progress,
                    "audio_file_url": audio_file_url,
                    "tempo": tempo
                })
                self.wfile.write(response.encode('utf-8'))
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "Invalid file path"}')
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            error_message = json.dumps({"error": str(e)})
            self.wfile.write(error_message.encode('utf-8'))

# Spuštění serveru na portu 5001
if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 5001
    with socketserver.TCPServer((HOST, PORT), MusicAnalysisHandler) as httpd:
        print(f"Serving on port {PORT}")
        httpd.serve_forever()
