const CACHE_NAME = "playtracker-v17";

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
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

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
