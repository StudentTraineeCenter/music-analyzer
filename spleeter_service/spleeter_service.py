import os
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import cgi

class SpleeterHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/process':
            # Parse the form data
            content_type, params = cgi.parse_header(self.headers['content-type'])
            if content_type != 'multipart/form-data':
                self.send_error(400, "Content type must be multipart/form-data")
                return
            
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            # Check for uploaded file
            if 'file' not in form:
                self.send_error(400, "No file uploaded")
                return
            
            file_item = form['file']
            filename = file_item.filename
            if not filename:
                self.send_error(400, "Uploaded file has no name")
                return

            # Save the uploaded file
            with open(filename, 'wb') as output_file:
                output_file.write(file_item.file.read())
            
            # Run Spleeter separation
            output_dir = 'output'
            os.makedirs(output_dir, exist_ok=True)
            command = ['spleeter', 'separate', '-i', filename, '-o', output_dir]
            
            response = {}
            try:
                subprocess.run(command, check=True)
                response = {'status': 'success', 'output_dir': output_dir}
            except subprocess.CalledProcessError as e:
                response = {'status': 'error', 'message': str(e)}
            
            # Clean up input file
            os.remove(filename)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))

def run_server(server_class=HTTPServer, handler_class=SpleeterHandler, port=5001):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting spleeter service on port {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
