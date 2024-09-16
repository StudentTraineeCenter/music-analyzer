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
    document.getElementById('loading-bar').querySelector('span').style.width = '100%';

    // Add YouTube link to FormData if available
    if (youtubeLink) {
        formData.append('youtubeLink', youtubeLink);
    }

    // Fetch request to analyze the file or link
    fetch('/analyze', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
            document.getElementById('loading').style.display = 'none'; // Hide loading bar
            
            if (data.error) {
                document.getElementById('error').innerText = 'Error: ' + data.error;
            } else {
                document.getElementById('results').innerHTML = `
                    <p>Tempo: ${data.tempo}</p>
                    <p>Instruments: ${data.instruments}</p>
                    <p>Notes: ${data.notes || 'N/A'}</p>
                    <p>Chords: ${data.chords || 'N/A'}</p>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('loading').style.display = 'none';
            document.getElementById('error').innerText = 'Error occurred during analysis.';
        });
});
