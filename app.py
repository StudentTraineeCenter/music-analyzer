import os
from flask import Flask, request, jsonify, render_template
import librosa
from pydub import AudioSegment
import numpy as np

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
        filename = file.filename
        file_path = os.path.join('uploads', filename)
        file.save(file_path)

        try:
            # Convert to WAV
            sound = AudioSegment.from_file(file_path)
            wav_path = file_path.replace('.mp3', '.wav')
            sound.export(wav_path, format="wav")

            # Analyze with librosa
            y, sr = librosa.load(wav_path)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

            if isinstance(tempo, (list, np.ndarray)):
                tempo = tempo[0]

            # Mock list of instruments for simplicity
            instruments = "drums, guitar, bass, vocals"

            # Cleanup
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
        # Add logic for handling YouTube link analysis here
        return jsonify({
            'tempo': 120,  # Mock response for now
            'instruments': "vocals, guitar"
        })

    return jsonify({'error': 'No file or link provided.'}), 400

if __name__ == "__main__":
    app.run(debug=True)
