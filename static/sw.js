const CACHE_NAME = "playtracker-v32";

// The install handler also precaches every generated category and play page
// returned by /api/offline-urls.
const urlsToCache = [
    "/",
    "/setup",
    "/category",
    "/saved_games",
    "/summary",
    "/static/style.css",
    "/static/manifest.json",
    "/static/storage.js",
    "/sw.js"
];

self.addEventListener("install", event => {
    self.skipWaiting();
    event.waitUntil(
        (async () => {
            const cache = await caches.open(CACHE_NAME);
            const response = await fetch("/api/offline-urls", { cache: "no-store" });
            if (!response.ok) {
                throw new Error(`Offline URL list request failed: ${response.status}`);
            }

            const data = await response.json();
            if (!Array.isArray(data.urls) || !data.urls.every(
                url => typeof url === "string" && url.startsWith("/")
            )) {
                throw new Error("Offline URL list is invalid.");
            }

            // Install only after every built-in page and generated play page
            // can be served offline; otherwise keep the previous worker active.
            await cache.addAll([...new Set([...urlsToCache, ...data.urls])]);
        })()
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
