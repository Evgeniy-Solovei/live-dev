/* LiveDev — precache; build.id читается один раз, без fetch на каждый запрос */

const CORE_ASSETS = [
  './',
  './index.html',
  './build.json',
  './assets/styles.css',
  './assets/site-layout.css',
  './assets/script.js',
  './assets/theme-switcher.js',
  './assets/sw-register.js',
  './assets/themes/theme-dark.css',
  './assets/themes/theme-light.css',
  './assets/themes/theme-ocean.css',
  './assets/themes/theme-backgrounds.css',
  './assets/themes/theme-overrides.css',
  './assets/themes/theme-switcher.css',
];

let activeCacheName = null;

const loadBuildId = () =>
  fetch('./build.json', { cache: 'no-store' })
    .then((res) => res.json())
    .then((build) => {
      activeCacheName = `livedev-${build.id}`;
      return activeCacheName;
    });

self.addEventListener('install', (event) => {
  event.waitUntil(
    loadBuildId()
      .then((cacheName) => caches.open(cacheName).then((cache) => cache.addAll(CORE_ASSETS)))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    loadBuildId()
      .then((current) =>
        caches.keys().then((keys) =>
          Promise.all(
            keys
              .filter((key) => key.startsWith('livedev-') && key !== current)
              .map((key) => caches.delete(key))
          )
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.endsWith('/build.json') || url.pathname.endsWith('/sw.js')) {
    event.respondWith(fetch(request));
    return;
  }

  if (!activeCacheName) {
    event.respondWith(fetch(request));
    return;
  }

  event.respondWith(
    caches.open(activeCacheName).then((cache) =>
      cache.match(request).then(
        (cached) =>
          cached ||
          fetch(request).then((response) => {
            if (response.ok) cache.put(request, response.clone());
            return response;
          })
      )
    )
  );
});
