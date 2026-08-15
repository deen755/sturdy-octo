// sw.js — AtmoSync EN Service Worker
// Lives at repo root, served at "/sw.js" by api/index.py — NOT inside
// /static/. A script served from "/" gets a default scope of "/", giving
// it control over the entire origin (app shell + /api/* calls), instead
// of being boxed into /static/ only.
// Job 1: cache the app shell so it boots instantly with zero network.
// Job 2: let /api/* calls fail cleanly so client.js can fall back to the
//        IndexedDB offline queue (db.js) — this file does NOT cache live
//        telemetry, only the static shell.

const CACHE_NAME = "atmosync-shell-v2";
const APP_SHELL = [
  "/static/index.html",
  "/static/style.css",
  "/static/client.js",
  "/static/db.js",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

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

  // App shell: cache-first for instant, offline-capable loads.
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});
