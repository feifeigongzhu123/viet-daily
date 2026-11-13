/* Offline cache for the VietDaily PWA. */
const CACHE = "vietdaily-v1.9.1";
const CORE = [
  "./",
  "./index.html",
  "./app.css",
  "./app.js",
  "./data/words.js",
  "./data/phonetics.js",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-512.png",
  "./icons/apple-touch-icon.png",
  "./icons/favicon-32.png",
  "./audio/index.json",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE);
      await cache.addAll(CORE);

      // Pre-cache all word and example MP3s with bounded concurrency. A
      // single failed file must not prevent the app shell from working offline.
      try {
        const response = await fetch("./audio/index.json", { cache: "reload" });
        if (response.ok) {
          const data = await response.json();
          const files = Array.isArray(data.files) ? data.files : [];
          let cursor = 0;
          const worker = async () => {
            while (cursor < files.length) {
              const file = files[cursor];
              cursor += 1;
              const url = `./${file}`;
              try {
                const audio = await fetch(url, { cache: "reload" });
                if (audio.ok) await cache.put(url, audio);
              } catch (error) {
                // Retry on first playback; audio is optional for install.
              }
            }
          };
          await Promise.all(Array.from({ length: 6 }, () => worker()));
        }
      } catch (error) {
        // Audio is optional for install; it will be cached on first use.
      }

      await self.skipWaiting();
    })(),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)));
      await self.clients.claim();
    })(),
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  const isAudio = url.pathname.includes("/audio/");

  // App shell and data are network-first so a new deployment is picked up
  // immediately. Audio is cache-first because it is immutable and large.
  if (!isAudio) {
    event.respondWith(
      (async () => {
        try {
          const response = await fetch(request);
          if (response && response.ok) {
            const cache = await caches.open(CACHE);
            cache.put(request, response.clone());
          }
          return response;
        } catch (error) {
          return (
            (await caches.match(request, { ignoreSearch: true })) ||
            (await caches.match("./index.html")) ||
            (await caches.match("./")) ||
            new Response("离线状态，请重新打开越词。", {
              status: 503,
              headers: { "Content-Type": "text/plain; charset=utf-8" },
            })
          );
        }
      })(),
    );
    return;
  }

  event.respondWith(
    (async () => {
      const cached = await caches.match(request, { ignoreSearch: true });
      if (cached) return cached;

      try {
        const response = await fetch(request);
        if (response && response.ok) {
          const cache = await caches.open(CACHE);
          cache.put(request, response.clone());
        }
        return response;
      } catch (error) {
        return (
          cached ||
          new Response("", { status: 504, statusText: "Offline" })
        );
      }
    })(),
  );
});
