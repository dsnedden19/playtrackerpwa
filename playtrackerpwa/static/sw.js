const CACHE_NAME = "playtracker-v11";

const urlsToCache = [
    "/",
    "/setup",
    "/category",
    "/saved_games",
    "/stat",
    "/plays",
    "/summary",
    "/static/style.css",
    "/static/manifest.json",
    "/static/storage.js"
];

self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener("fetch", event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => response || fetch(event.request))
    );
});
