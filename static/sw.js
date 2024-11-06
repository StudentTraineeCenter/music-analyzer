self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open('static-v1').then(function(cache) {
            return cache.addAll([
                '/',
                '/static/styles.css',  // Add the paths to your static files that should be cached
                '/static/app.js'
            ]);
        })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request).then(function(response) {
            return response || fetch(event.request);
        })
    );
});
