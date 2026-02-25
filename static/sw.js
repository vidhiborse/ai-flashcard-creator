// Service Worker for AI Flashcard Creator
// Version 1.0

const CACHE_NAME = 'flashcard-cache-v1';
const urlsToCache = [
    '/static/style.css',
    '/static/dark-mode.css'
];

// Install event - cache files
self.addEventListener('install', event => {
    console.log('Service Worker: Installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Service Worker: Caching files');
                return cache.addAll(urlsToCache);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean old caches
self.addEventListener('activate', event => {
    console.log('Service Worker: Activating...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cache => {
                    if (cache !== CACHE_NAME) {
                        console.log('Service Worker: Deleting old cache:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
    return self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
    // Only cache GET requests
    if (event.request.method !== 'GET') {
        return;
    }
    
    // Skip caching for API calls
    if (event.request.url.includes('/api/') || 
        event.request.url.includes('/toggle-') ||
        event.request.url.includes('/logout')) {
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Return cached version or fetch from network
                return response || fetch(event.request)
                    .then(fetchResponse => {
                        // Cache static resources for future
                        if (event.request.url.includes('/static/')) {
                            return caches.open(CACHE_NAME).then(cache => {
                                cache.put(event.request, fetchResponse.clone());
                                return fetchResponse;
                            });
                        }
                        return fetchResponse;
                    });
            })
            .catch(() => {
                // Fallback for offline - return basic error
                if (event.request.destination === 'document') {
                    return new Response(
                        '<h1>Offline</h1><p>You are currently offline. Please check your connection.</p>',
                        { headers: { 'Content-Type': 'text/html' } }
                    );
                }
            })
    );
});