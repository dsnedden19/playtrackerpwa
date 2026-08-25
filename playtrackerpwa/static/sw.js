const CACHE_NAME = "playtracker-v6";

const urlsToCache = [
    "/",
    "/setup",
    "/category",
    "/summary",
    "/plays/Man%20Offense",
    "/plays/Zone%20Offense",
    "/plays/Blob",
    "/plays/Slob",
    "/plays/Defense",
    "/static/style.css",
    "/static/manifest.json",
    "/static/storage.js"
];

self.addEventListener("install", event => {
    self.skipWaiting();

    event.waitUntil(
        caches.open(CACHE_NAME).then(async cache => {
            await cache.addAll(urlsToCache);

            const response = await fetch("/offline-urls");
            const statUrls = await response.json();

            await cache.addAll(statUrls);
        })
    );
});

self.addEventListener("activate", event => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", event => {
    if (event.request.method !== "GET") {
        return;
    }

    event.respondWith(
        caches.match(event.request).then(cachedResponse => {
            if (cachedResponse) {
                return cachedResponse;
            }

            return fetch(event.request).then(networkResponse => {
                const responseCopy = networkResponse.clone();

                caches.open(CACHE_NAME).then(cache => {
                    cache.put(event.request, responseCopy);
                });

                return networkResponse;
            });
        })
    );
});
