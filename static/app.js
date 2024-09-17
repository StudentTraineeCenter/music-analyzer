document.getElementById('uploadForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const formData = new FormData(this);
    const fileInput = document.getElementById('fileInput').files.length > 0;
    const youtubeLink = document.getElementById('youtubeLink').value.trim();

    // Check if either file or YouTube link is provided
    if (!fileInput && !youtubeLink) {
        document.getElementById('error').innerText = 'Please provide a file or a YouTube link.';
        return;
    }

    // Show loading bar
    document.getElementById('loading').style.display = 'block';
    document.getElementById('loading-bar').querySelector('span').style.width = '0%';  // Start at 0%

    // Add YouTube link to FormData if available
    if (youtubeLink) {
        formData.append('youtubeLink', youtubeLink);
    }

    // Create a new XMLHttpRequest
    const xhr = new XMLHttpRequest();

    // Track upload progress
    xhr.upload.addEventListener('progress', function(e) {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            document.getElementById('loading-bar').querySelector('span').style.width = percentComplete + '%';
        }
    });

    // Set up the request
    xhr.open('POST', '/analyze', true);

    // Define what happens on successful data submission
    xhr.onload = function() {
        document.getElementById('loading').style.display = 'none';
        if (xhr.status >= 200 && xhr.status < 300) {
            const response = JSON.parse(xhr.responseText);
            if (response.error) {
                document.getElementById('error').innerText = response.error;
            } else {
                document.getElementById('results').innerText = `Tempo: ${response.tempo} BPM\nInstruments: ${response.instruments}`;
            }
        } else {
            document.getElementById('error').innerText = 'Error analyzing the file.';
        }
    };

    // Define what happens in case of an error
    xhr.onerror = function() {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').innerText = 'An error occurred.';
    };

    // Send the request with the form data
    xhr.send(formData);
});
