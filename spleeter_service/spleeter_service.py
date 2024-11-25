
from flask import Flask, request, jsonify
import os
import subprocess

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_audio():
    # Ensure the file is received
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    filename = file.filename
    file.save(filename)
    
    # Run Spleeter separation
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    command = ['spleeter', 'separate', '-i', filename, '-o', output_dir]
    
    try:
        subprocess.run(command, check=True)
        response = {'status': 'success', 'output_dir': output_dir}
    except subprocess.CalledProcessError as e:
        response = {'status': 'error', 'message': str(e)}
    
    # Clean up input file
    os.remove(filename)
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
