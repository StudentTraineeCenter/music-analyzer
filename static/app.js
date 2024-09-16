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

    // Handle response
    xhr.onload = function() {
        document.getElementById('loading').style.display = 'none';  // Hide loading bar
        const data = JSON.parse(xhr.responseText);

        if (xhr.status === 200 && !data.error) {
            document.getElementById('results').innerHTML = `
                <p>Tempo: ${data.tempo}</p>
                <p>Instruments: ${data.instruments}</p>
                <p>Notes: ${data.notes || 'N/A'}</p>
                <p>Chords: ${data.chords || 'N/A'}</p>
            `;
        } else {
            document.getElementById('error').innerText = 'Error: ' + (data.error || 'Unknown error occurred.');
        }
    };

    xhr.onerror = function() {
        document.getElementById('loading').style.display = 'none';  // Hide loading bar
        document.getElementById('error').innerText = 'Error occurred during analysis.';
    };

    // Open the request and send the form data
    xhr.open('POST', '/analyze');
    xhr.send(formData);
});
