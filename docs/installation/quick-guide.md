🌐 **English** · [Deutsch](quick-guide.de.md) · [한국어](quick-guide.ko.md) · [Español](quick-guide.es.md) · [Português (Brasil)](quick-guide.pt-BR.md) · [Français](quick-guide.fr.md)

# Quick Install Guide

For people comfortable with a terminal, Docker, and a small amount of sysadmin. If that's not you, the [Beginner Guide](beginner.md) covers the same ground at a slower pace with more handholding.

Time required: **30–60 minutes** from a fresh server to a logged-in admin. Most of that is the first `docker compose up --build`, which builds the two Moimio images from source on your machine.

---

## Prerequisites

- A Linux host (any modern distro — Ubuntu 22.04+, Debian 12+, Fedora, anything systemd).
- **Docker Engine 24+** and **Docker Compose v2** (the `docker compose` subcommand, not the legacy `docker-compose` standalone).
- **Git** (for cloning) — or just download and unpack the source tarball.
- **Ports:** `6120` (frontend; it also proxies `/api` and `/health` to the backend, so browsers only ever need this one). Compose also publishes `6121` (backend, for direct API access during debugging) and `6122` (PostgreSQL). Neither needs to be public; see "Changing the ports" below for binding them to localhost.
- `sudo` rights for `upgrade.sh`, which calls `sudo docker compose`.
- Roughly **2 GB RAM** and **5 GB disk** for a small church-scale deployment.

To check Docker is ready:

```bash
docker --version          # → Docker version 24.0+ ...
docker compose version    # → Docker Compose version v2.x.x
```

If `docker compose version` fails, you have the legacy standalone Compose. Install the v2 plugin: `apt install docker-compose-plugin` (Ubuntu/Debian) or follow [Docker's official instructions](https://docs.docker.com/compose/install/).

---

## 1. Clone and configure

```bash
git clone https://github.com/pistio/moimio.git
cd moimio
cp .env.example .env
```

Open `.env` and edit at minimum the first two of these:

| Variable | What to set |
|---|---|
| `SECRET_KEY` | A random string of **at least 64 characters**. Generate one with `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` or `openssl rand -hex 64`. **Do not leave the `change-me-...` placeholder in production.** |
| `POSTGRES_PASSWORD` | A random password for the database user. Same generation method. |
| `DATABASE_URL` | Optional. `docker-compose.yml` builds the backend's `DATABASE_URL` from `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB`, so the line in `.env` is not what the container uses. Update its password segment anyway if you like the file to be consistent. |

Set `POSTGRES_PASSWORD` **before the first start.** Postgres only applies it when the `pgdata` volume is first created; changing it later produces `password authentication failed` until you change it inside the database too.

Leave `LOG_LEVEL=INFO` (the default). See "Production hardening" for why.

If you want email out of the box, also set the SMTP block — see the SMTP table at the bottom of this guide. Skipping SMTP is fine; the app runs without it (registration confirmation emails just don't get sent, and admins can confirm registrations by hand).

### Changing the ports

The defaults are 6120 (frontend), 6121 (backend), 6122 (Postgres). If any of these are already in use on your host, override them in `.env`:

```
FRONTEND_PORT=7120
BACKEND_PORT=7121
DB_PORT=7122
```

`docker-compose.yml` reads these via `${FRONTEND_PORT:-6120}` etc., so the env values flow through without further edits. You'd then open `http://localhost:7120` instead.

The values are dropped straight into Compose's `ports:` mapping, so you can also give an address. This binds the port to the host's loopback interface only:

```
BACKEND_PORT=127.0.0.1:6121
DB_PORT=127.0.0.1:6122
# Only when your reverse proxy or tunnel runs on this same host:
FRONTEND_PORT=127.0.0.1:6120
```

The browser talks to the backend through the frontend's `/api` proxy, so changing `BACKEND_PORT` needs nothing else. (Older `.env` files may still contain `VITE_API_URL`; nothing reads it, so you can delete the line.)

---

## 2. Start the stack

![Terminal output during docker compose up build](../assets/install-docker-build.png)

```bash
docker compose up -d --build
```

First run pulls images and builds — expect 3–5 minutes on a decent connection. Subsequent rebuilds are faster.

Watch the backend come up:

```bash
docker compose logs -f backend
```

You're looking for two log lines, in order:

```
INFO  [alembic.runtime.migration] Running upgrade ... -> <latest migration>
INFO  Application startup complete.
```

The first means the database schema was created/migrated successfully. The second means uvicorn is serving the API. If you see the second without the first, migrations were already up to date — also fine. **Press Ctrl-C to stop following the log; the containers keep running.**

Smoke-test the API (the same endpoint is also reachable through the frontend at `http://localhost:6120/health`):

```bash
curl http://localhost:6121/health
# → {"status":"ok","database":"healthy","version":"1.0.6"}
```

### About those Alembic migrations

Alembic is a database migration tool that ships with SQLAlchemy. It manages schema evolution: each migration file is a versioned change-set that knows how to bring the database forward (and, where possible, backward).

Two things worth knowing:

- **Migrations run automatically every time the backend container starts.** The Dockerfile's CMD is `alembic upgrade head && uvicorn ...` — Alembic checks the database's current revision and applies any newer migrations it finds, then hands off to uvicorn.
- **Migrations don't wipe your data.** Each migration is incremental: "add this column", "create this table", "rename this index". They never recreate the database from scratch. As long as you don't run `docker compose down -v` (the `-v` flag deletes named volumes including `moimio_pgdata`), your participant data, events, and allocations are preserved across upgrades.

If you ever do need to reset the database, that's `docker compose down -v` (it removes the `pgdata` volume, named `<project>_pgdata`, e.g. `moimio_pgdata`). Do this only on a deployment with no real data.

---

## 3. Create the first admin

![First-time setup wizard for the initial Super Admin account](../assets/first-time-setup.png)

Moimio doesn't ship with a default admin. Open `http://localhost:6120` (or whatever port you've configured) in a browser. You'll land on a **first-time setup screen** automatically — Moimio detects that no users exist and offers the wizard.

Fill in:

- **Full name** — display name in the admin UI.
- **Email** — your login.
- **Password** and **Confirm password** — minimum 8 characters. Use a real password manager.

The screen also has a language picker and a light/dark toggle. Click **Create Super Admin**. The account is created with the **Super Admin** role, and you're taken to the sign-in page to log in with it. The setup screen never appears again once any user exists.

**Alternative — CLI bootstrap.** For headless deployments or scripted provisioning, the same operation is available from the command line:

```bash
docker compose exec backend python -m app.cli.create_admin
```

It prompts for email, full name and password, and creates a Super Admin. On-screen is the recommended default for self-hosters. The CLI is also the way back in if you lose the only Super Admin password and have no SMTP for a reset: create a second Super Admin with a different email.

---

## 4. Log in (after setup)

Sign in at `http://localhost:6120/login` with the account you just created.

With no events yet you land on the **Welcome to Moimio** screen; click **Create your first event**. Once events exist, the events list has a **+ New Event** button.

As Super Admin, also open **Workspace** in the sidebar and set your **Privacy notice URL**. The public registration form links to it right after the consent sentence; leave it empty and no link is shown.

---

## 5. Production hardening

Before exposing Moimio to the public internet:

- Put a TLS-terminating reverse proxy in front of port 6120. Caddy, Traefik, or a Cloudflare Tunnel on the host all work well; Nginx + Let's Encrypt is the classic option.
- HTTPS is also what makes the in-app features work. Browsers register the service worker only on HTTPS or on `localhost`, so an install opened on a plain-HTTP LAN address such as `http://192.168.1.20:6120` gets no offline caching, no "new version available" prompt and nothing for the "Clear cache and reload" button to clear, and no error anywhere says why.
- Keep the backend port (6121) and the database port (6122) off the public internet. Bind them to localhost in `.env` (see "Changing the ports"). A host firewall rule alone is not enough: ports Docker publishes are opened in iptables by Docker itself and bypass `ufw`/`firewalld` rules.
- Read [`SECURITY.md`](../../SECURITY.md) — the "Hardening recommendations for self-hosters" section covers the rest (strong SECRET_KEY, DB password rotation, Docker host patching, SMTP credential discipline).
- Leave `LOG_LEVEL=INFO` on any install that holds real participants. `LOG_LEVEL=DEBUG` writes participant names, addresses and dates of birth to the container log on every request; debug on a copy with invented data instead.

---

## 6. Updating

From the repo root of your git clone:

```bash
./upgrade.sh                # latest commit on your current branch
./upgrade.sh v1.0.6         # a specific release tag (see CHANGELOG.md)
./upgrade.sh v1.0.6 --yes   # skip the confirmation prompt
./upgrade.sh --dry-run      # show what would happen, change nothing
```

The script checks first (`.env` present, clean working tree, `db` container running), shows the commits it will apply, backs up `.env` to `.env.pre-upgrade-<timestamp>.bak` and the database to `../pgdata-pre-upgrade-<timestamp>.sql.gz`, then checks out the target and runs `docker compose down`, `build --no-cache` and `up -d`. It prints the exact rollback commands at the end. Keep the backups until you're happy with the new version. Checking out a tag leaves the clone on a detached HEAD, so once you've pinned a version, name the next one explicitly too (`./upgrade.sh v1.0.7`) rather than running it bare.

After restarting, the script waits up to 90 seconds for the backend container to report "healthy". The backend's healthcheck in `docker-compose.yml` calls `/health` every 10 seconds after a 30-second start period. If the wait ends in a "did not become healthy" warning (for example a long migration), check `curl http://localhost:6121/health` and the backend log before rolling back.

The manual equivalent, if you prefer:

```bash
git pull            # or: git fetch --tags && git checkout v1.0.6
docker compose build --no-cache
docker compose up -d --force-recreate
```

`--no-cache` matters when the Dockerfile changes (new dependencies, font installs, etc.). If you skip it, you may end up running new code against an old image layer and hit confusing failures.

Migrations run automatically on backend startup — no manual `alembic upgrade head` step needed. Your data is preserved across upgrades (the `pgdata` volume is not touched). Take a backup first anyway, as with any upgrade.

`deploy.sh` in the repo root is a different tool: it replaces the install from a packaged `../moimio-ce-<tag>.zip` and is meant for installs that were not made with `git clone`. If you cloned the repo, use `upgrade.sh`.

### Container images

This guide builds the images from source. Each release is also published as `ghcr.io/pistio/moimio-backend:<tag>` and `ghcr.io/pistio/moimio-frontend:<tag>` (for example `v1.0.6`). If you use them, always pin a version tag: `:latest` is frozen at v1.0.6, no longer moves, and is not supported. `backend/deploy/production.yml` is the hosted service's template, not a self-hosting compose file; use the root `docker-compose.yml`.

---

## 7. Backups

The simplest backup is a Postgres `pg_dump`:

```bash
docker compose exec -T db pg_dump -U moimio moimio | gzip > moimio-backup-$(date +%F).sql.gz
```

Run this on a cron schedule. Store the dumps somewhere off the host.

To restore, load the dump into an empty database (a plain dump piped into a populated database fails on existing tables and rows):

```bash
docker compose stop backend
docker compose exec -T db dropdb -U moimio moimio
docker compose exec -T db createdb -U moimio moimio
gunzip -c moimio-backup-2026-10-01.sql.gz | docker compose exec -T db psql -U moimio moimio
docker compose start backend
```

(Substitute your `POSTGRES_USER` / `POSTGRES_DB` if you changed them.)

The product also ships an in-app event-level backup: the **Backup** page in the sidebar downloads one ZIP per event (full, or structure only with no personal data), and **Restore from backup** brings one back as a new draft event, on this or another deployment. Team members and their roles are not carried in a backup; invite the team again on the receiving server. See [`docs/manual/09-data-export-gdpr.md`](../manual/09-data-export-gdpr.md) in the user manual.

For a whole-workspace archive from the command line: `docker compose exec backend python -m app.cli.export_all --out /tmp/moimio-export.zip`.

To bring a whole workspace onto this server, every event in one go, see [Moving a workspace to your own Moimio](../moving-a-workspace.md).

---

## SMTP reference (optional)

If you want registration confirmation emails and password resets, fill in the SMTP block in `.env`:

```
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=events@yourchurch.org
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=events@yourchurch.org
SMTP_FROM_NAME=Your Church Events
SMTP_TLS=true
SMTP_SSL=false
```

`SMTP_TLS=true` is STARTTLS (port 587). For implicit TLS on port 465, set `SMTP_PORT=465`, `SMTP_SSL=true` and `SMTP_TLS=false`. Email is switched on only when both `SMTP_HOST` and `SMTP_USER` are set. Restart the backend after changing any of these (`docker compose up -d backend`).

Common providers and their typical settings (verify against the provider's current documentation — these change occasionally):

| Provider | Typical host | Typical port | Notes |
|---|---|---|---|
| Zoho Mail | `smtp.zoho.eu` / `smtp.zoho.com` | 587 | Generate an app password under Account → Security |
| Gmail / Google Workspace | `smtp.gmail.com` | 587 | Requires 2FA + app password |
| Brevo (formerly Sendinblue) | `smtp-relay.brevo.com` | 587 | Free tier covers most small-church volumes |
| SMTP2GO | `mail.smtp2go.com` | 587 | Pay-as-you-go with a free tier |
| Mailgun | `smtp.mailgun.org` | 587 | Requires domain verification |

**Always check your provider's own current SMTP documentation** before configuring — settings, port numbers, and authentication requirements change. A provider's status page is the source of truth, not this table.

Test from the UI after creating an event: open the event's registration form settings (**Setup ▸ Registration** while the event is in setup, **More ▸ Registration form** once registration is open), then **Email confirmation ▸ Send Test Email**. The test email goes to your own login address and states which `From` name, `Reply-To`, and SMTP server were used — most useful for diagnosing "the email never arrived" cases.

If SMTP is left empty, the app skips sending and logs `email_skipped` for each would-be send. Useful for development.

---

## Optional settings reference

All of these are read from `.env` and passed through by `docker-compose.yml`. Restart with `docker compose up -d` after changing them.

| Variable | Default | What it does |
|---|---|---|
| `LOG_LEVEL` | `INFO` | `DEBUG` logs every database query with its values, i.e. participant data. |
| `RATE_LIMIT_REGISTRATION` | `60` | Sign-ups per minute from one address. Each extra family member on the form counts. Raise it if a whole congregation registers over one Wi-Fi at once; `0` turns it off. Behind your own reverse proxy or Cloudflare Tunnel the real visitor address is used, as long as that proxy reaches Moimio from a private or loopback address and sends `X-Forwarded-For`. |
| `FEATURE_ALLOCATION` | `true` | `false` turns off the allocation engine for a registration-only install. |
| `FEATURE_OUTBOUND_WEBHOOKS` | `true` | `false` hides the Webhooks page and disables delivery. See [webhooks](../webhooks.md). |
| `WEBHOOK_ALLOW_PRIVATE_TARGETS` | `false` | Webhook URLs on private, loopback or link-local addresses (`10.x`, `192.168.x`, `localhost`…) are refused unless this is `true`. Set it only if your receiver lives on your own network. Not in `.env.example`; add the line yourself. |
| `WEBHOOK_DELIVERY_RETENTION_DAYS` | `30` | How long webhook delivery history is kept. |

The remaining variables in `.env.example` and `docker-compose.yml` (`FEATURE_CREATE_EVENT_CONFIRMATION`, `EVENT_CHARGE_*`, `BILLING_CARD_LAST4`, `FEATURE_ACCOUNT_PORTAL`, `ACCOUNT_URL`, `FEATURE_DEMO_NOTICE`, `MOIMIO_DEMO_MAIL_URL`, `MOIMIO_TENANT_ID`, `MOIMIO_WEBHOOK_URL`, `MOIMIO_WEBHOOK_SECRET`) exist for the hosted service and its demo workspaces. Leave them at their defaults on a normal self-hosted install. `APP_URL` is no longer used: email links take their address from the request.

---

## Troubleshooting

**`docker compose up` exits immediately, no logs.**
Check the actual error: `docker compose ps` then `docker compose logs <service>`. The most common cause is a port conflict — something else on the host is already using 6120, 6121, or 6122. Either stop the conflicting service or change the port (see "Changing the ports" above).

**Backend logs show `connection refused` to `db:5432`.**
The backend started before Postgres was ready. The `depends_on: condition: service_healthy` clause normally prevents this — if you're seeing it, your Docker version may be too old. Update Docker, or just `docker compose restart backend`.

**Backend logs show `relation "users" does not exist`.**
Alembic migrations didn't run. Check `docker compose logs backend` for an Alembic error earlier in the log. The fix is usually `docker compose down && docker compose up -d --force-recreate`.

**The page says "Cannot reach the server", or login fails with a network error.**
The frontend container serves the page and proxies `/api/*` to the backend container. Check that the backend is up (`docker compose ps`, then `docker compose logs backend`) and that `curl http://localhost:6120/health` answers. If you put your own reverse proxy in front, make sure it forwards every path to port 6120, not just `/`.

**Backend logs show `password authentication failed for user "moimio"`.**
`POSTGRES_PASSWORD` was changed after the database volume was first created; Postgres keeps the original. Put the old password back in `.env`, or change it inside the database (`docker compose exec db psql -U moimio -c "ALTER USER moimio PASSWORD '<new>'"`) and restart.

**Anything else.**
Open a [bug report](https://github.com/pistio/moimio/issues/new?template=bug_report.md) with the relevant logs (mask any participant data first).

---

Ready to use Moimio? Start with the [User Manual](../manual/README.md) for the event-organising workflow.
