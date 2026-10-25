🌐 **English** · [Deutsch](README.de.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português (Brasil)](README.pt-BR.md) · [Français](README.fr.md)

# Installation

This guide covers installing **Moimio CE (Community Edition)**, the open-source self-hostable build. (For the managed hosted product, sign up at [moimio.app](https://moimio.app) — no installation required.)

Moimio CE runs as three Docker containers (a backend, a frontend, a database) orchestrated by Docker Compose. Installation is mostly: clone, configure, `docker compose up --build` (which builds the Moimio images from source on your machine), then create the first admin via the on-screen setup screen.

There are two guides in this folder, depending on your background. Pick one.

---

## Which guide should I follow?

### → [Quick Install Guide](quick-guide.md)

Use this if you already know:

- What Docker is and how to run `docker compose` commands.
- How to SSH into a server, edit a file, and read logs.
- How to set up a TLS-terminating reverse proxy (Caddy, Nginx, Traefik, or a Cloudflare Tunnel).

Time required: **30–60 minutes** from cloning to a logged-in admin.

### → [Beginner Guide](beginner.md)

Use this if any of the above sounds unfamiliar. The beginner guide:

- Walks through the **two main hosting options** — a rented VPS (cloud server) or your own computer/mini-PC at home or office, with Cloudflare Tunnel for public access.
- Teaches the SSH workflow from scratch, including key generation.
- Installs Docker via the official one-liner, with no assumptions.
- Configures Moimio step by step, with explanations of what each piece is for.
- Covers domain names and HTTPS via Caddy or Cloudflare.

Time required: **about 2 hours** the first time, mostly waiting.

You don't need to be a developer to follow it. You need to be willing to copy commands carefully and ask for help when something doesn't work.

---

## What it'll cost

Hosting costs depend entirely on where you put it.

| Where | Cost | Suits |
|---|---|---|
| Your own laptop / desktop (for trial) | Free | Trying Moimio out, learning the workflow. Not suitable for real events because the laptop has to stay on. |
| A church-owned mini PC at the office | One-time hardware (€150–300) | Small church running a few events a year. Works as long as the office has stable power and internet. |
| A rented VPS at any cloud provider | ~€4–10 per month | Most users. Always-on, easy to scale up. EU-hosted options exist for GDPR-conscious organisers. |

You'll also want a **domain name** (€10–15 per year) for real-world registration links — we walk through this in the beginner guide.

---

## Hardware requirements

Moimio's footprint is small. Indicative numbers:

- **CPU:** Any modern x86_64 or ARM64 processor. Two cores is enough.
- **RAM:** **2 GB minimum**, 4 GB comfortable. Memory usage scales gently with concurrent registration traffic.
- **Disk:** **5 GB** for the application images and database; the database itself grows slowly (Moimio stores no file uploads).
- **Network:** A public IP (or a tunnel like Cloudflare Tunnel) is needed for participants to reach the registration form. Inbound port 80/443 (or 6120 if you skip TLS for testing). For real events, plan on HTTPS: some in-app features (offline caching, the "new version available" prompt) only work over HTTPS or on `localhost`.

To verify the host you're considering meets these:

- **CPU + architecture:** `uname -m` (Linux/macOS) or look at "System type" in About this PC (Windows). Anything that returns `x86_64`, `aarch64`, or `arm64` is fine.
- **RAM:** `free -h` (Linux), Activity Monitor (macOS), Task Manager → Performance (Windows).
- **Disk free:** `df -h` (Linux/macOS), File Explorer → This PC (Windows).
- **Public reachability:** if it's a VPS, the provider tells you the public IP; if it's your own computer, see the beginner guide's section on Cloudflare Tunnel.

A small VPS with 2 vCPU and 2 GB RAM (commonly priced around €4–5/month with European providers) handles a 150-person event without strain. A **Raspberry Pi 4 (4 GB)** also works for small events run from a church office. Both are examples — Moimio doesn't require any specific hardware or hosting provider.

---

## Operating system

Anywhere Docker runs:

- **Linux** (Ubuntu 22.04+, Debian 12+, Fedora, Arch, ...) — recommended for production.
- **macOS** with Docker Desktop — fine for development; not recommended for events you're charging registrations against (laptops aren't servers).
- **Windows** with Docker Desktop and WSL2 — same caveat.

---

## After installation

Once Moimio is running, your browser will land on the **First-time setup** screen automatically. Fill in your full name, email and a password (twice), click **Create Super Admin**, then sign in with the account you just made. With no events yet, you'll see a **Welcome to Moimio** screen with a **Create your first event** button.

Two things worth doing early:

- **Set your privacy notice link.** As Super Admin, open **Workspace** in the sidebar and enter the web address of your organisation's privacy notice. The public registration form then links to it right after the consent sentence.
- **Plan upgrades and backups.** Both guides have a short section on each. In short: `./upgrade.sh` upgrades a git install and takes a database backup first; the in-app **Backup** page downloads per-event backups.

Moving from the hosted service or another server? See [Moving a workspace to your own Moimio](../moving-a-workspace.md).

From there, the [User Manual](../manual/README.md) walks through actually running an event: creating events, configuring registration, running the allocation engine, doing check-in, exporting rosters.

If you hit problems during installation, the troubleshooting sections at the bottom of each guide cover the common failures. Anything weirder than that, [open a bug report](https://github.com/pistio/moimio/issues/new?template=bug_report.md).
