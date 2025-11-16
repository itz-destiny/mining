self.addEventListener('install', function(event) {
  event.waitUntil(self.skipWaiting());
});
self.addEventListener('activate', function(event) {
  event.waitUntil(self.clients.claim());
});
self.addEventListener('fetch', function(event) {
  // Basic network-first strategy
  event.respondWith(fetch(event.request).catch(function() {
    return caches.match(event.request);
  }));
});
