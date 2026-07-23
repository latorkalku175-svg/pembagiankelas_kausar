// GuruKelas PWA Service Worker
const CACHE_NAME = 'gurukelas-v1';
const OFFLINE_URL = '/login/';

// Assets to cache on install
const PRECACHE_ASSETS = [
  '/',
  '/login/',
  '/static/css/style.css',
  '/static/manifest.json',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
];

// Install: pre-cache core assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('[SW] Pre-cache failed for some assets:', err);
      });
    })
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Fetch: network-first strategy for HTML, cache-first for static assets
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and cross-origin requests
  if (request.method !== 'GET' || url.origin !== location.origin) return;

  // Skip admin and API-like requests
  if (url.pathname.startsWith('/admin/')) return;

  // Cache-first for static assets (CSS, JS, images, icons)
  if (
    url.pathname.startsWith('/static/') ||
    url.pathname.startsWith('/media/')
  ) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        });
      })
    );
    return;
  }

  // Network-first for HTML pages (with offline fallback)
  event.respondWith(
    fetch(request)
      .then((response) => {
        // Cache successful page responses
        if (response.ok && request.headers.get('accept')?.includes('text/html')) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return response;
      })
      .catch(() => {
        // Offline fallback: serve cached version or login page
        return caches.match(request).then(
          (cached) => cached || caches.match(OFFLINE_URL)
        );
      })
  );
});
