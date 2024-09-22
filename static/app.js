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

// Progress bar polling
setInterval(function() {
    fetch('/progress')
        .then(response => response.json())
        .then(data => {
            document.getElementById('loading-bar').querySelector('span').style.width = data.progress + '%';
        });
}, 1000);

// Audio controls
const audioContext = new (window.AudioContext || window.webkitAudioContext)();
const gainNodes = {};

const loadAudio = (source, label) => {
    const audioElement = new Audio(source);
    const sourceNode = audioContext.createMediaElementSource(audioElement);
    const gainNode = audioContext.createGain();

    sourceNode.connect(gainNode);
    gainNode.connect(audioContext.destination);
    gainNodes[label] = gainNode;

    audioElement.play();

    audioElement.addEventListener('ended', () => {
        fetch('/cleanup', { method: 'POST' });
    });
};

const setVolume = (label, volume) => {
    if (gainNodes[label]) {
        gainNodes[label].gain.setValueAtTime(volume, audioContext.currentTime);
    }
};

document.querySelectorAll('.volume-slider').forEach(slider => {
    slider.addEventListener('input', function() {
        const volume = parseFloat(this.value);
        const label = this.dataset.track;
        setVolume(label, volume);
    });
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    navigator.sendBeacon('/cleanup');
});
