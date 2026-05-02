# Multistage build. Stage 1 builds the static bundle with Vite;
# stage 2 serves it with Caddy (which also reverse-proxies /api/*
# and /health to the backend container).
#
# This is a true production build, not a `vite dev` server. PWA
# features (service worker, generated manifest) require a built
# bundle. Local frontend development should run `npm run dev` on
# the host workstation rather than relying on container hot-reload;
# this container has no source volume mount, so host edits do not
# affect the running build.
#
# Build size: minified + gzipped via Caddy.

# --- Stage 1: build ---
FROM node:20-alpine AS build

WORKDIR /app

# Python 3 is required by `npm run build` — the i18n key validator
# (frontend/scripts/validate-i18n-keys.py) runs as a pre-step to vite
# build, blocking the image build if any t('foo.bar') callsite
# references a key not present in en.json. Catches the dot-vs-
# underscore class of bug before deploy.
RUN apk add --no-cache python3

# Install deps from the lock file. `npm ci` is strict — it errors if
# package.json and package-lock.json disagree, which is what we want
# in a reproducible build. Falls back to npm install if no lock
# exists (shouldn't normally happen since we ship a lock file).
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy source and run Vite's production build. Produces /app/dist
# with hashed asset filenames.
COPY . .
RUN npm run build

# --- Stage 2: runtime ---
FROM caddy:2-alpine

# Caddy looks at /etc/caddy/Caddyfile by default (see the caddy
# image's CMD). We ship our Caddyfile there, and the build output
# at /srv which is Caddy's conventional web-root on Alpine.
COPY --from=build /app/dist /srv
COPY Caddyfile /etc/caddy/Caddyfile

# Port 5173 to match the pre-existing docker-compose port mapping
# (6120:5173). Keeping the internal port stable means the compose
# file doesn't need editing just for the topology change.
EXPOSE 5173
