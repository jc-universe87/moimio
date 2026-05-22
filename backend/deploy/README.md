# `backend/deploy/` — production compose template for the hosted SaaS

This directory contains the Docker Compose template that the **Moimio
SaaS provisioning driver** uses to spin up per-tenant stacks on the
hosted product. It is not used by self-hosters.

## What's here

- **`production.yml`** — the compose template. References pinned
  GHCR image tags, declares two networks, no host port publishing,
  no source mounts, healthchecks on all three services.
- **`README.md`** — this file.

## Where this file lives in the running system

After CE is built and pushed to GHCR, this file rides inside the
backend image at `/app/deploy/production.yml`. The SaaS provisioning
driver reads it from there (no Git clone required at provisioning
time). See `20260521_moimio-saas-v0.4.0-architecture.md` §6 for the
full architecture rationale.

## How it relates to the dev compose at the project root

Two compose files, two purposes:

| File | Used by | Mode |
|---|---|---|
| `/docker-compose.yml` (project root) | Self-hosters and local development | Builds images from source. Source mounts. Host port publishing for direct access. |
| `/backend/deploy/production.yml` (this file) | SaaS provisioning driver only | References pre-built GHCR images. No source mounts. No host ports (Caddy routes via Docker DNS). |

The two files describe the **same three services** (db, backend,
frontend) with the **same architectural shape**. They differ only in
the deployment posture appropriate for each environment.

## How it relates to the `/deploy.sh` script at the project root

`/deploy.sh` is the self-hoster bootstrap script — it walks a new
self-hoster through fetching CE, configuring `.env`, and running
the dev compose to get a single-tenant install up on their own
hardware. It has nothing to do with this directory.

The naming overlap is unfortunate. To be unambiguous:

- **`/deploy.sh`** = a one-shot script self-hosters run on their server.
- **`/backend/deploy/`** = a deployment artefact the hosted SaaS uses.

## Network names

```
moimio-${SUBDOMAIN}-internal   per-tenant   db + backend + frontend
moimio-public                  shared       frontend + outer Caddy
```

The `moimio-public` network is created **once** on the production
host during initial setup (`docker network create moimio-public`).
Per-tenant `moimio-${SUBDOMAIN}-internal` networks are created and
torn down by Compose on each `up`/`down` cycle.

The backend container is reachable **only** from inside its tenant's
internal network. The outer Caddy on the public network has no path
to it — only to the frontend, which reverse-proxies `/api/*` and
`/health` to the backend over the internal network.

## Environment variables

The SaaS provisioner writes a per-tenant `.env` file alongside
`production.yml` before running `docker compose up`. The required
variables (`:?` syntax in the compose) refuse to start the stack if
missing. The optional variables (`:-default` syntax) fall back to
sensible defaults.

### Required (provisioner must set these per tenant)

| Variable | Purpose | Example |
|---|---|---|
| `SUBDOMAIN` | Tenant subdomain. Used in network name. | `cmi-germany` |
| `POSTGRES_USER` | Postgres database user. | `moimio_cmi_germany` |
| `POSTGRES_PASSWORD` | Postgres database password. Generated per tenant. | (random 32-char string) |
| `POSTGRES_DB` | Postgres database name. | `moimio` |
| `SECRET_KEY` | FastAPI session secret. Generated per tenant. | (random 64-char string) |
| `CORS_ORIGINS` | Allowed CORS origins for the backend API. | `https://cmi-germany.moimio.app` |
| `FEATURE_ALLOCATION` | Capability flag — `true` for hosting tier, `false` for registration tier. | `true` |
| `SMTP_HOST` | SMTP relay hostname. | `in-v3.mailjet.com` |
| `SMTP_USER` | SMTP username (Mailjet API key). | (from provisioner config) |
| `SMTP_PASSWORD` | SMTP password (Mailjet API secret). | (from provisioner config) |
| `SMTP_FROM_EMAIL` | "From" address for outbound mail. | `noreply@moimio.app` |
| `MOIMIO_TENANT_ID` | SaaS-side tenant identifier. UUID or similar. | (from SaaS registry) |
| `MOIMIO_WEBHOOK_URL` | URL the backend posts outbound webhooks to (the SaaS). | `http://saas:8000/webhooks/ce` |
| `MOIMIO_WEBHOOK_SECRET` | HMAC signing secret for CE → SaaS webhooks. | (random 32-char string) |

### Optional (provisioner may set, otherwise defaults apply)

| Variable | Default | Purpose |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Backend log verbosity. |
| `RATE_LIMIT_REGISTRATION` | `10` | Registrations per minute per IP. |
| `SMTP_PORT` | `587` | SMTP relay port. |
| `SMTP_FROM_NAME` | `Moimio` | Display name on outbound mail. |
| `SMTP_TLS` | `true` | STARTTLS for SMTP. |
| `SMTP_SSL` | `false` | Implicit SSL for SMTP. |
| `FEATURE_OUTBOUND_WEBHOOKS` | `true` | Whether the backend emits CE → SaaS webhooks. |
| `FEATURE_CREATE_EVENT_CONFIRMATION` | `false` | Stripe-style event-create confirmation flow. |
| `EVENT_CHARGE_AMOUNT` | `` | Per-event charge amount shown in UI. |
| `EVENT_CHARGE_CURRENCY` | `` | Per-event charge currency. |
| `BILLING_CARD_LAST4` | `` | Last 4 digits of billing card, shown in UI. |
| `WEBHOOK_DELIVERY_RETENTION_DAYS` | `30` | Days before delivered webhooks are purged. |

## Responsibility boundary: SaaS provisioner ↔ CE

The provisioner owns:

- Writing the per-tenant `.env` file with all required values.
- Generating per-tenant secrets (`POSTGRES_PASSWORD`, `SECRET_KEY`,
  `MOIMIO_WEBHOOK_SECRET`).
- Maintaining a copy of `MOIMIO_WEBHOOK_SECRET` in the SaaS registry
  (per Secrets Option 1 in the v0.4.0 ADR — the only secret
  duplicated, used for inbound webhook verification).
- Creating the `moimio-public` network during initial setup.
- Running `docker compose -f production.yml up -d`.
- Polling Docker for healthcheck status before marking the tenant active.
- Running the deprovision sequence on cancellation (`docker compose
  down` without `-v`; volume removal happens in a separate erasure
  step after the 44-day GDPR grace period).

CE (the application) owns:

- The runtime behaviour described by the env vars passed in.
- Alembic migrations on startup (idempotent — runs every container
  start, does nothing if already at head).
- Emitting outbound webhooks to `MOIMIO_WEBHOOK_URL` signed with
  `MOIMIO_WEBHOOK_SECRET`.
- Not knowing or caring that it's running in a multi-tenant context.

## Image versions

The two `image:` lines in `production.yml` reference specific GHCR
tags (`ghcr.io/jc-universe87/moimio-backend:v1.0.0m` and similarly
for frontend). These tags are bumped together each CE release.
Never `:latest` — pinning is enforced.

For SaaS upgrade of a tenant: render the newer release's
`production.yml` into the tenant's compose directory, then run
`docker compose pull && docker compose up -d`. Volume persists,
database persists, only the running containers replace.
