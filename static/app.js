let isAnalyzing = false;
let progressInterval;

document.getElementById('uploadForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const formData = new FormData(this);
    const fileInput = document.getElementById('fileInput').files.length > 0;

    if (!fileInput) {
        document.getElementById('error').innerText = 'Please provide a file.';
        return;
    }

    document.getElementById('error').innerText = ''; // Clear previous error
    document.getElementById('loading').style.display = 'block';
    document.getElementById('loading-bar').querySelector('span').style.width = '0%';

    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', function(e) {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            document.getElementById('loading-bar').querySelector('span').style.width = percentComplete + '%';
        }
    });

    xhr.open('POST', '/analyze', true);

    xhr.onload = function() {
        document.getElementById('loading').style.display = 'none';
        isAnalyzing = false; // Set flag to false when analysis is done

        if (xhr.status >= 200 && xhr.status < 300) {
            const response = JSON.parse(xhr.responseText);
            if (response.error) {
                document.getElementById('error').innerText = response.error;
            } else if (response.redirect_url) {
                window.location.href = response.redirect_url;
            }
        } else {
            document.getElementById('error').innerText = 'Error analyzing the file.';
        }
    };

    xhr.onerror = function() {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').innerText = 'An error occurred.';
    };

    xhr.send(formData);

    // Set isAnalyzing and start polling
    isAnalyzing = true;
    if (!progressInterval) {
        progressInterval = setInterval(function() {
            if (isAnalyzing) {
                fetch('/progress')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('loading-bar').querySelector('span').style.width = data.progress + '%';
                        if (data.progress >= 100) {
                            clearInterval(progressInterval);
                            progressInterval = null; // Reset interval
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching progress:', error);
                        clearInterval(progressInterval); // Stop interval on error
                        progressInterval = null;
                    });
            } else {
                clearInterval(progressInterval); // Stop polling if analysis is not active
            }
        }, 2000);
    }
});
