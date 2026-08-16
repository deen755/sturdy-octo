// sw.js — AtmoSync EN Service Worker
// Lives at repo root, served at "/sw.js" by api/index.py — NOT inside
// /static/. A script served from "/" gets a default scope of "/", giving
// it control over the entire origin (app shell + /api/* calls), instead
// of being boxed into /static/ only.
// Job 1: cache the app shell so it boots instantly with zero network.
// Job 2: let /api/* calls fail cleanly so client.js can fall back to the
//        IndexedDB offline queue (db.js) — this file does NOT cache live
//        telemetry, only the static shell.

const CACHE_NAME = "atmosync-shell-v3";
const APP_SHELL = [
  "/static/index.html",
  "/static/style.css",
  "/static/client.js",
  "/static/db.js",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

// --- Install: pre-cache the app shell, one file at a time ---
// cache.addAll() is all-or-nothing: if ONE url in the list 404s, the whole
// install rejects and the worker never activates — which is exactly what
// silently broke offline mode last time (missing icon files). Caching each
// file individually means a single bad path degrades gracefully (logged,
// skipped) instead of taking the entire offline experience down with it.
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      Promise.all(
        APP_SHELL.map((url) =>
          cache.add(url).catch((err) => {
            console.error(`[sw] failed to precache ${url}:`, err);
          })
        )
      )
    )
  );
  self.skipWaiting();
});

// --- Activate: clean up old caches ---
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// --- Fetch strategy ---
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Live telemetry: network-first, no caching of readings here.
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(event.request).catch(
        () =>
          new Response(JSON.stringify({ offline: true, error: "network unavailable" }), {
            headers: { "Content-Type": "application/json" },
            status: 503,
          })
      )
    );
    return;
  }

  // Navigations (address-bar loads, redirects, launching from home screen):
  // try cache first, then network, and if BOTH fail, fall back to the
  // cached app shell itself rather than letting the request fail through
  // to Chrome's native offline interstitial. This is the actual fix for
  // "browser's default offline banner instead of the app" — it's a
  // last-resort safety net on top of the app-shell precache above.
  if (event.request.mode === "navigate") {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) return cached;
        return fetch(event.request).catch(() =>
          caches.match("/static/index.html")
        );
      })
    );
    return;
  }

  // Everything else (CSS/JS/images): cache-first for instant, offline loads.
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});
