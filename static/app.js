// Přidej tento flag pro sledování stavu analýzy
let isAnalyzing = false;
let progressInterval;

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
        isAnalyzing = false; // Nastavit flag na false, když analýza skončí

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

    // Nastav isAnalyzing a spusť polling
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
                            progressInterval = null; // Resetuj interval
                        }
                    });
            } else {
                clearInterval(progressInterval); // Ukončit polling, pokud není analýza aktivní
            }
        }, 2000);
    }
});
