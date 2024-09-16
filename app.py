import os
from flask import Flask, request, jsonify, render_template
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

    if file:
        # Nahrání a analýza MP3 souboru
        filename = file.filename
        file_path = os.path.join('uploads', filename)
        file.save(file_path)

        try:
            # Konverze na WAV
            sound = AudioSegment.from_file(file_path)
            wav_path = file_path.replace('.mp3', '.wav')
            sound.export(wav_path, format="wav")

            # Analýza pomocí librosa
            y, sr = librosa.load(wav_path)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

            if isinstance(tempo, (list, np.ndarray)):
                tempo = tempo[0]

            # Mock list of instruments
            instruments = "drums, guitar, bass, vocals"

            # Úklid
            os.remove(file_path)
            os.remove(wav_path)

            return jsonify({
                'tempo': float(tempo),
                'instruments': instruments
            })

        except Exception as e:
            print(f"Error during processing: {e}")
            return jsonify({'error': str(e)}), 500

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
                mp3_filename = f"uploads/{info_dict['id']}.mp3"

            # Konverze na WAV
            sound = AudioSegment.from_file(mp3_filename)
            wav_path = mp3_filename.replace('.mp3', '.wav')
            sound.export(wav_path, format="wav")

            # Analýza pomocí librosa
            y, sr = librosa.load(wav_path)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

            if isinstance(tempo, (list, np.ndarray)):
                tempo = tempo[0]

            # Mock list of instruments
            instruments = "drums, guitar, bass, vocals"

            # Úklid
            os.remove(mp3_filename)
            os.remove(wav_path)

            return jsonify({
                'tempo': float(tempo),
                'instruments': instruments
            })

        except Exception as e:
            print(f"Error during YouTube processing: {e}")
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'No file or link provided.'}), 400

if __name__ == "__main__":
    app.run(debug=True)
