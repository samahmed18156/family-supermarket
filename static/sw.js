/* Family Supermarket - PWA Service Worker - FREE
   Offline cart, installable, performance boost
   v3 - Retreat supermarket SEO + 063 837 8201
*/
const CACHE_NAME = 'family-market-v3-0638378201';
const OFFLINE_URL = '/';

const ASSETS_TO_CACHE = [
  '/',
  '/specials',
  '/about',
  '/retreat-supermarket',
  '/static/style.css',
  '/static/script.js',
  '/static/cart.js',
  '/static/images/rice.jpg',
  '/static/images/vegetables.jpg',
  '/static/images/bread.jpg',
  '/manifest.json'
];

// Install - cache assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE.map(url => new Request(url, {cache: 'reload'})));
    })
  );
  self.skipWaiting();
});

// Activate - clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)));
    })
  );
  self.clients.claim();
});

// Fetch - Network first, cache fallback, offline cart
self.addEventListener('fetch', (event) => {
  const { request } = event;
  
  // Skip API and admin
  if (request.url.includes('/api/') || request.url.includes('/admin') || request.url.includes('/inquiries')) {
    return;
  }

  // For pages - network first
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).then((response) => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
        return response;
      }).catch(() => {
        return caches.match(request).then(cached => cached || caches.match(OFFLINE_URL));
      })
    );
    return;
  }

  // For assets - cache first, network fallback
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        // Cache new assets
        if (response.ok && request.method === 'GET' && !request.url.includes('chrome-extension')) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
        }
        return response;
      }).catch(() => {
        // Offline fallback for images
        if (request.destination === 'image') {
          return new Response('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect width="200" height="200" fill="#f1f5f9"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#94a3b8" font-family="sans-serif" font-size="14">Family Market</text></svg>', {headers: {'Content-Type': 'image/svg+xml'}});
        }
      });
    })
  );
});

// Background sync for orders (when back online)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-orders') {
    event.waitUntil(syncOrders());
  }
});

async function syncOrders() {
  // Try to send cached orders when online
  const cache = await caches.open(CACHE_NAME);
  // Implementation for future - FREE offline orders
}
