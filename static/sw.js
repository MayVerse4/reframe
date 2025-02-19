self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open("reframe-cache").then((cache) => {
            return cache.addAll([
                '/welcome',
                '/static/logo.png'
            ]);
        })
    );
});

self.addEventListener("fetch", (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});
