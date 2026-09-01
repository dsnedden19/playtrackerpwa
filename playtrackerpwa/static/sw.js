const CACHE_NAME = "playtracker-v22";

// Only routes that exist with no URL params. Dynamic pages
// (/stat/<cat>/<play>, /plays/<cat>) get cached on first visit instead —
// see the fetch handler below.
const urlsToCache = [
    "/",
    "/setup",
    "/category",
    "/saved_games",
    "/summary",
    "/static/style.css",
    "/static/manifest.json",
    "/static/storage.js",
    "/static/icon-192.png",
    "/static/icon-512.png",
    "/sw.js"
];

self.addEventListener("install", event => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then(async cache => {
            for (const url of urlsToCache) {
                try {
                    await cache.add(url);
                } catch (err) {
                    console.error("FAILED to precache:", url, err);
                }
            }
        })
    );
});

// Clean up old cache versions so they don't pile up forever.
self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(names =>
            Promise.all(
                names
                    .filter(name => name !== CACHE_NAME)
                    .map(name => caches.delete(name))
            )
        ).then(() => self.clients.claim())
    );
});

self.addEventListener("fetch", event => {
    const { request } = event;

    // Never touch the Cache API for non-GET requests (POST to
    // /api/upload-game, etc.) — Cache.put() only supports GET, and
    // stat submits are already handled client-side via IndexedDB,
    // so these should just go straight to the network.
    if (request.method !== "GET") {
        event.respondWith(
            fetch(request).catch(err => {
                console.log("Network request failed (offline):", request.url, err);
                return new Response(
                    JSON.stringify({ success: false, message: "Offline" }),
                    { status: 503, headers: { "Content-Type": "application/json" } }
                );
            })
        );
        return;
    }

    event.respondWith(
        caches.match(request).then(cached => {
            if (cached) {
                return cached;
            }

            return fetch(request)
                .then(response => {
                    // Only cache successful, same-origin responses.
                    if (!response || response.status !== 200 || response.type !== "basic") {
                        return response;
                    }

                    const responseToCache = response.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(request, responseToCache);
                    });

                    return response;
                })
                .catch(err => {
                    console.log("Network request failed (offline):", request.url, err);

                    // Only fall back to the shell for page navigations —
                    // not for images/scripts/stylesheets that simply
                    // weren't cached yet.
                    if (request.mode === "navigate") {
                        return caches.match("/");
                    }

                    return new Response("", { status: 504, statusText: "Offline" });
                });
        })
    );
});
