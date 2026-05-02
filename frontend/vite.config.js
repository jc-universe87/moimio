import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import { readFileSync } from 'fs'
import { resolve } from 'path'

// v0.58i: derive MOIMIO_VERSION from frontend/package.json's
// `moimioVersion` field at build time so the sidebar version marker
// can never drift from the release tag. We use a custom field instead
// of `version` because our display tag uses suffix letters (v0.58g,
// v0.58g-1) that aren't valid semver, and `version` needs to stay
// valid semver for any tooling that reads it.
// Release workflow: bump "moimioVersion" in package.json once per ship.
// The sidebar picks it up automatically on next `docker compose build`.
function readMoimioVersion() {
  try {
    const pkg = JSON.parse(readFileSync(resolve(__dirname, 'package.json'), 'utf-8'))
    return pkg.moimioVersion || 'dev'
  } catch {
    return 'dev'
  }
}

const MOIMIO_VERSION = readMoimioVersion()

export default defineConfig({
  plugins: [
    react(),
    // v0.59d: Progressive Web App — service worker + generated manifest.
    //
    // Strategy:
    //   - Shell-only precache (HTML, JS, CSS, fonts, icons from the Vite
    //     build graph). No /api responses are ever cached.
    //   - NetworkOnly for /api/* and /health — confirms no stale API
    //     data is served under any circumstance. Offline behaviour:
    //     the shell loads, but API-dependent features show their usual
    //     error banners.
    //   - CacheFirst for fonts.bunny.net — fonts are stable and
    //     expensive; caching makes the offline shell visually correct.
    //   - User-triggered updates: new SW installs, sits in "waiting"
    //     state, our UpdatePrompt component surfaces a toast. User
    //     taps "Refresh" -> we post `skipWaiting` and reload. Avoids
    //     the classic "user stuck on old version" footgun of
    //     auto-activating new SWs mid-interaction.
    //
    // Cache-bust mechanics: Vite fingerprints every chunk filename
    // (e.g. `index-abc123.js`). Workbox precaches by fingerprint, so
    // old chunks are invalidated naturally on next build. The SW
    // script itself is versioned by its own hash; `cleanupOutdatedCaches`
    // removes stale precache stores on SW activation.
    //
    // Topology: depends on v0.59c's production-build-via-Caddy setup.
    // The plugin generates sw.js + manifest.webmanifest + registerSW
    // entries in dist/ during `vite build`; Caddy serves them verbatim.
    VitePWA({
      // 'prompt' installs a new SW on each build and surfaces it via
      // `needRefresh` in the client, but LEAVES IT IN WAITING STATE
      // until the client explicitly posts skipWaiting. This is what
      // UpdatePrompt's useRegisterSW/updateServiceWorker flow drives.
      //
      // Important: 'autoUpdate' would INTERNALLY force skipWaiting +
      // clientsClaim to true, bypassing our user-gated flow — the
      // new SW would take over mid-session on next navigation. For a
      // tool that organisers use during live events, that's wrong:
      // we want the user to choose when to reload.
      registerType: 'prompt',

      // Default auto-inject would add a <script> that registers the
      // SW. We set to null because UpdatePrompt uses the useRegisterSW
      // hook, which handles registration itself. Avoids double-registration.
      injectRegister: null,

      // Assets in /public/ that aren't referenced in the Vite build
      // graph but must still be precached by the SW.
      includeAssets: [
        'favicon.svg',
        'apple-touch-icon.png',
        'icon-192.png',
        'icon-512.png',
        'icon-512-maskable.png',
        'logogram.svg',
        'logogram-navy.svg',
      ],

      // Plugin-generated manifest replaces the hand-written one shipped
      // in v0.59b. Single source of truth — keeping a file + plugin
      // config in sync across ships was an easy-to-miss footgun.
      manifest: {
        name: 'Moimio — Gather · Organise',
        short_name: 'Moimio',
        description: 'Self-hostable, GDPR-first event and retreat management for churches and similar organisations. Turn registrations into organised rooms, groups, and teams with a preference-aware allocation engine.',
        id: '/',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        display_override: ['standalone', 'minimal-ui', 'browser'],
        orientation: 'any',
        // theme_color + background_color are fixed at light-mode --app-bg.
        // Manifests don't support media-query variants; the live meta
        // `theme-color` tags in index.html still adapt to dark mode
        // for the browser chrome on mobile Safari/Chrome.
        theme_color: '#F7F5F2',
        background_color: '#F7F5F2',
        lang: 'en',
        dir: 'ltr',
        categories: ['productivity', 'business'],
        prefer_related_applications: false,
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
          { src: '/icon-512-maskable.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },

      workbox: {
        // Precache globs — match what Vite emits in dist/. Workbox
        // computes hashes for each and serves them offline.
        globPatterns: ['**/*.{js,css,html,svg,png,ico,webmanifest}'],

        // Single-page-app routing: navigations to arbitrary paths
        // return index.html so React Router can handle them offline.
        navigateFallback: '/index.html',

        // ...except for API and health paths, which must hit network.
        // Without these rules the SW would serve index.html for /api
        // requests, breaking fetch() semantics (JSON parse would fail).
        navigateFallbackDenylist: [/^\/api\//, /^\/health$/],

        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.startsWith('/api/'),
            handler: 'NetworkOnly',
            options: { cacheName: 'moimio-api-no-cache' },
          },
          {
            urlPattern: ({ url }) => url.pathname === '/health',
            handler: 'NetworkOnly',
            options: { cacheName: 'moimio-health-no-cache' },
          },
          // Bunny.net font CDN — cache-first with a 30-day expiry.
          // Fonts are stable and expensive to refetch; caching them
          // makes the offline shell visually correct, not just functional.
          {
            urlPattern: /^https:\/\/fonts\.bunny\.net\//,
            handler: 'CacheFirst',
            options: {
              cacheName: 'moimio-fonts',
              expiration: { maxEntries: 12, maxAgeSeconds: 60 * 60 * 24 * 30 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],

        // Remove precache stores from previous Workbox versions on SW
        // activation. Belt-and-braces — Vite's fingerprinting already
        // handles content versioning, but if Workbox itself updates
        // we want a clean cache state.
        cleanupOutdatedCaches: true,

        // We want explicit user consent before activating a new SW.
        // skipWaiting=false means the new SW waits until the client
        // tells it via postMessage (we do this from updateServiceWorker
        // in UpdatePrompt). clientsClaim=false means the new SW only
        // controls clients after reload — not mid-interaction.
        skipWaiting: false,
        clientsClaim: false,
      },

      devOptions: {
        // Keep SW off during `vite dev` (local workstation development).
        // Workbox precaching conflicts with HMR and makes local dev
        // confusing — you'd hit stale cached files.
        enabled: false,
      },
    }),
  ],
  define: {
    __MOIMIO_VERSION__: JSON.stringify(MOIMIO_VERSION),
  },
  build: {
    // v0.61c: manual vendor split. The pre-v0.61c build emitted a
    // single ~965 KB main chunk because React, react-router, qrcode,
    // and all app code shipped together — Vite warned at the 500 KB
    // soft cap. Splitting React + qrcode into their own chunks lets
    // browsers cache them separately across deploys (changing app
    // code no longer invalidates the React bundle) and reduces what
    // a first-load critical path has to parse before paint.
    //
    // We only split node_modules. App code stays in one chunk because
    // route-level lazy loading would add per-page network round-trips
    // for an app most users access over a fast LAN or a tunnel that's
    // already paid the connection cost.
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          // React + its router + scheduler internals → react-vendor.
          // The regex is anchored to a node_modules path segment so
          // it can't accidentally match an app-code module that
          // happens to have "react" in its name.
          if (/[\\/]node_modules[\\/](react|react-dom|react-router|react-router-dom|scheduler)[\\/]/.test(id)) {
            return 'react-vendor'
          }
          // qrcode is only used in ShareFormModal. Splitting keeps
          // it out of the critical path for the dashboard / board /
          // check-in flows where it's never touched.
          if (/[\\/]node_modules[\\/]qrcode[\\/]/.test(id)) {
            return 'qrcode'
          }
          return 'vendor'
        },
      },
    },
    // Soft cap raised to 750 KB. Post-split, the main app chunk
    // lands at ~711 KB (~176 KB gzipped) — bigger than the 500 KB
    // Vite default but bounded by app code (247 source files,
    // translations.json ~250 KB), not vendor bloat. Further shrinking
    // would need route-level lazy loading (a real architectural
    // change, not polish) or splitting translations.json per-language
    // (adds a round-trip on language switch). Both are v0.70 audit
    // territory — for now we just stop warning on the size we
    // actually have.
    chunkSizeWarningLimit: 750,
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    historyApiFallback: true,
    // Proxy config — only used by `vite dev` (local workstation).
    // In production deployment the frontend container runs Caddy,
    // which handles /api and /health proxying via its own reverse_proxy
    // config (see frontend/Caddyfile, v0.59c).
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})
