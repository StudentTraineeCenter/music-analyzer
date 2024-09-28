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
    document.getElementById('loadingText').style.display = 'block';
    document.getElementById('loadingContainer').style.display = 'block';
    document.getElementById('loadingBar').style.width = '0%';

    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', function(e) {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            document.getElementById('loadingBar').style.width = percentComplete + '%';
        }
    });

    xhr.open('POST', '/analyze', true);

    xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
            // Zahájíme polling na progress
            isAnalyzing = true;
            startProgressPolling();
        } else {
            document.getElementById('error').innerText = 'Error analyzing the file.';
            document.getElementById('loadingText').style.display = 'none';
            document.getElementById('loadingContainer').style.display = 'none';
        }
    };

    xhr.onerror = function() {
        document.getElementById('loadingText').style.display = 'none';
        document.getElementById('loadingContainer').style.display = 'none';
        document.getElementById('error').innerText = 'An error occurred.';
    };

    xhr.send(formData);
});

function startProgressPolling() {
    if (!progressInterval) {
        progressInterval = setInterval(function() {
            fetch('/progress')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('loadingBar').style.width = data.progress + '%';
                    if (data.progress >= 100) {
                        clearInterval(progressInterval);
                        progressInterval = null;
                        window.location.href = '/results'; // Přesměrování až po 100% dokončení
                    }
                })
                .catch(error => {
                    console.error('Error fetching progress:', error);
                    clearInterval(progressInterval);
                    progressInterval = null;
                });
        }, 2000); // Pollování každou sekundu
    }
}
// Příklad volání po změně posuvníku hlasitosti
document.querySelectorAll('.volume-slider').forEach(slider => {
    slider.addEventListener('input', () => {
        // Po změně hlasitosti obnovíme audio
        reloadAudio();
    });
});

