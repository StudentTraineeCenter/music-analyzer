import os
import shutil
from flask import Flask, request, jsonify, render_template, url_for
import librosa
from pydub import AudioSegment
import numpy as np
import yt_dlp

app = Flask(__name__)

UPLOADS_FOLDER = 'uploads'
TEMPORARY_UPLOADS_FOLDER = 'temporary_uploads'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files.get('file')
    youtube_link = request.form.get('youtubeLink')

    if not os.path.exists(UPLOADS_FOLDER):
        os.makedirs(UPLOADS_FOLDER)
    if not os.path.exists(TEMPORARY_UPLOADS_FOLDER):
        os.makedirs(TEMPORARY_UPLOADS_FOLDER)

    file_path = None
    if file:
        # Nahrání a analýza MP3 souboru
        filename = file.filename
        file_path = os.path.join(UPLOADS_FOLDER, filename)
        file.save(file_path)

    elif youtube_link:
        try:
            # Stáhnout audio pomocí yt-dlp
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
            # Konverze na WAV
            sound = AudioSegment.from_file(file_path)
            wav_path = file_path.replace('.mp3', '.wav')
            sound.export(wav_path, format="wav")

            # Analýza pomocí librosa
            y, sr = librosa.load(wav_path, sr=None)  # sr=None udržuje původní vzorkovací frekvenci
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

            if isinstance(tempo, (list, np.ndarray)):
                tempo = tempo[0]

            instruments = ["Nástroj 1", "Nástroj 2", "Nástroj 3"]  # Mock list of instruments

            # Přesun souborů do dočasné složky
            temp_audio_path = os.path.join(TEMPORARY_UPLOADS_FOLDER, os.path.basename(file_path))
            temp_wav_path = os.path.join(TEMPORARY_UPLOADS_FOLDER, os.path.basename(wav_path))
            shutil.move(file_path, temp_audio_path)
            shutil.move(wav_path, temp_wav_path)

            # Vráti URL na dočasné soubory
            audio_url = url_for('static', filename=os.path.basename(temp_audio_path))

            return jsonify({
                'redirect_url': url_for('results', tempo=tempo, instruments=','.join(instruments), audio_file_url=audio_url)
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'No file or link provided.'}), 400

@app.route('/results')
def results():
    tempo = request.args.get('tempo')
    instruments = request.args.get('instruments').split(',')
    audio_file_url = request.args.get('audio_file_url')
    return render_template('results.html', tempo=tempo, instruments=instruments, audio_file_url=audio_file_url)

@app.route('/cleanup')
def cleanup():
    for filename in os.listdir(TEMPORARY_UPLOADS_FOLDER):
        file_path = os.path.join(TEMPORARY_UPLOADS_FOLDER, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    return 'Cleanup done'

if __name__ == "__main__":
    app.run(debug=True)
