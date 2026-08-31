const CACHE_NAME = "playtracker-v20";

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
    "/static/storage.js",
    "/sw.js"
];

self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(async cache => {
            for (const url of urlsToCache) {
                try {
                    await cache.add(url);
                    console.log("Cached:", url);
                } catch (err) {
                    console.error("FAILED:", url, err);
                }
            }
        })
    );
});

self.addEventListener("fetch", event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                if (response) {
                    return response;
                }

                return fetch(event.request)
                    .then(networkResponse => {
                        return networkResponse;
                    })
                    .catch(() => {

                        const url = new URL(event.request.url);

                        if (url.pathname.startsWith("/plays/")) {
                            return caches.match("/category");
                        }

                        if (url.pathname.startsWith("/stat/")) {
                            return caches.match("/category");
                        }

                        return caches.match("/");
                    });
            })
    );
});
