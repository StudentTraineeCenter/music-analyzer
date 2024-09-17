import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
import librosa
from pydub import AudioSegment
import numpy as np
import yt_dlp

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files.get('file')
    youtube_link = request.form.get('youtubeLink')

    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    file_path = None
    if file:
        # Nahrání a analýza MP3 souboru
        filename = file.filename
        file_path = os.path.join('uploads', filename)
        file.save(file_path)

    elif youtube_link:
        try:
            # Stáhnout audio pomocí yt-dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'uploads/%(id)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_link, download=True)
                file_path = f"uploads/{info_dict['id']}.mp3"

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

            # Úklid
            os.remove(file_path)
            os.remove(wav_path)

            # Přesměrování na stránku s výsledky
            return jsonify({
                'redirect_url': url_for('results', tempo=tempo, instruments=','.join(instruments))
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'No file or link provided.'}), 400

@app.route('/results')
def results():
    tempo = request.args.get('tempo')
    instruments = request.args.get('instruments').split(',')
    return render_template('results.html', tempo=tempo, instruments=instruments)

if __name__ == "__main__":
    app.run(debug=True)
