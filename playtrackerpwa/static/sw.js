const CACHE_NAME = "playtracker-v21";

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
    console.log("FETCH:", event.request.url);

    event.respondWith(
        caches.match(event.request)
            .then(response => {
                if (response) {
                    console.log("CACHE HIT:", event.request.url);
                    return response;
                }

                console.log("NETWORK:", event.request.url);

                return fetch(event.request).catch(err => {
                    console.log("FAILED:", event.request.url, err);

                    return caches.match("/");
                });
            })
    );
});
