document.getElementById('uploadForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const formData = new FormData(this);
    const fileInput = document.getElementById('fileInput').files.length > 0;
    const youtubeLink = document.getElementById('youtubeLink').value.trim();

    if (!fileInput && !youtubeLink) {
        document.getElementById('error').innerText = 'Please provide a file or a YouTube link.';
        return;
    }

    document.getElementById('loading').style.display = 'block';
    document.getElementById('loading-bar').querySelector('span').style.width = '0%';

    if (youtubeLink) {
        formData.append('youtubeLink', youtubeLink);
    }

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
});
