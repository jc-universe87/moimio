# Beginner Install Guide

This guide is for someone who's never opened a terminal but needs Moimio running for a real event. We'll go slowly.

If you're already comfortable with Docker and Linux servers, the [Quick Install Guide](quick-guide.md) covers the same ground in 30 minutes.

You don't need to be a developer. You need to be willing to copy commands carefully and ask for help when something doesn't work.

---

## A note on honesty before we start

Installing Moimio is more involved than installing a desktop app. There's no "click the button, wait, done" experience yet. If you hit something the guide doesn't cover, asking a more technical friend or pasting the error into ChatGPT or Claude will usually get you unstuck in a few minutes.

The first time you do this, plan for **about two hours**. Most of that is waiting for downloads. The second time, it's much faster.

---

## Should you self-host? A reality check

Installation is the easy part. The harder question is what running a production server looks like in the months that follow — especially during a live event when something breaks and you need it back in twenty minutes.

A self-hosted Moimio is a small Linux server you are now responsible for. Concretely, that means:

- **The server has to stay on.** If your office loses power, the venue Wi-Fi goes down, or the VPS provider has an outage — registration is offline until you bring it back.
- **Updates need applying.** New Moimio versions, security patches to Ubuntu, occasional Docker updates. Not weekly, but not zero.
- **Things will fail at inconvenient times.** SSL certificate renewal can fail; a database migration can refuse to run after an update; the database container can refuse to restart. The fix is usually one or two commands — *if you know which commands*.
- **Backups are your problem.** Moimio has a backup feature, but actually running it before a major change, and storing the result somewhere safe, is on you.
- **DNS, certificates, and tunnels are operationally fragile.** A domain expires, an IP changes, a Cloudflare token rotates — and the registration form goes 404.

**A self-assessment.** Before continuing, please check honestly:

- [ ] You're comfortable running terminal commands and reading error output.
- [ ] If a service won't start, you know how to find and read its logs.
- [ ] If the server's IP address changes, you know how to update DNS.
- [ ] If something breaks at 11pm during the event, you have someone (or the skills) to fix it.
- [ ] You have a backup strategy, not just an intention.

**If any of these is *no*, please consider [moimio.app](https://moimio.app) — the managed hosted version of the same product.** It runs the same code, the same allocation engine, the same registration flow. Hosting, backups, updates, and SSL are handled. Current pricing is on the website.

This guide will continue to walk you through self-hosting if you want it. The cost of self-hosting is not the few euros a month for a VPS — it's the on-call posture during a live event. Make the decision with your eyes open.

---

## Pick your hosting path

There are two reasonable ways to run Moimio. Pick whichever fits your situation:

### → Path A — Rent a small server (a "VPS")

A VPS is a small computer that lives in a data centre, that you rent by the month and access remotely. Costs €4–10 per month. Always on, always reachable, no equipment to maintain at your end.

**Best if:** you want low ongoing maintenance, you're running registrations months in advance, or you don't want a computer at home tied up running Moimio.

Continue at [Path A — VPS setup](#path-a--rent-a-vps) below.

### → Path B — Self-host on your own computer or mini-PC

Run Moimio on a computer you already own, then expose it to the internet through a free service called Cloudflare Tunnel. Zero hosting fees.

**Best if:** data sovereignty is a hard constraint (you specifically need participant data on hardware you own), and you have someone who can troubleshoot a Linux machine during an event.

A home or office host is materially less reliable than a VPS. Power, internet, the cloudflared connector, and the host OS itself can fail; the registration form goes offline until someone gets to the machine and fixes it. If data sovereignty isn't a hard requirement, Path A (VPS) or [moimio.app](https://moimio.app) are simpler choices.

Continue at [Path B — Self-host with Cloudflare Tunnel](#path-b--self-host-with-cloudflare-tunnel) below.

Both paths converge at **[Step 4 — Install Moimio](#step-4--install-moimio)**, which is the same regardless of where Moimio is running.

---

## Path A — Rent a VPS

A VPS provider gives you a small computer in a data centre. There are many — Hetzner, OVH, Scaleway, DigitalOcean, Linode, Vultr, Contabo, and many regional providers. Most charge €4–10/month for what Moimio needs.

For European church / mission organisations, providers with European data centres are often preferable for GDPR reasons (your participants' data stays in the EU). Hetzner Cloud (in Germany / Finland) and OVH (in France / Germany) are common picks. For organisers in Korea, Japan, the US, or elsewhere, your local cloud provider is usually fine — Moimio doesn't care which one you choose.

> **Not endorsing a specific provider.** This guide gives Hetzner Cloud as an *example* because it's well-documented and inexpensive — not as a recommendation. Pick whoever you trust. The setup is similar everywhere.

### Step 1 — Sign up and create the server

Each VPS provider has its own signup and provisioning flow. Rather than re-document a step-by-step that goes stale every time the provider redesigns their console, follow your provider's own getting-started documentation.

For Hetzner Cloud specifically: <https://docs.hetzner.com/cloud/servers/getting-started/creating-a-server/>

When you create the server, the choices that matter for Moimio:

- **Operating system:** **Ubuntu 24.04** (or 22.04) — these are the easiest to get help for if anything goes wrong.
- **Server size:** Roughly **2 vCPU + 2 GB RAM + 40 GB disk** is plenty for a 150-person event. Most providers call this their "small" tier and charge €4–5/month.
- **SSH key:** Add your SSH key during creation (so you can connect without a password). If you don't have one yet, jump to [Step 2 — Generate an SSH key](#step-2--generate-an-ssh-key) before creating the server, then come back.
- **Location:** Pick a data centre close to where your participants are. EU data centres are typically preferable for European events; for events elsewhere, pick whatever's geographically and legally appropriate.

Once the server is created, the provider gives you a **public IP address** (something like `203.0.113.42`). **Write that IP address down** — you'll need it to connect.

### Step 2 — Generate an SSH key

An SSH key is two matching files: a **public key** (which you give to your VPS provider) and a **private key** (which stays on your laptop, like a digital house key). Together they let your laptop log into the server without a password.

On your laptop, open a terminal:

- **macOS:** Spotlight → "Terminal".
- **Linux:** any terminal app.
- **Windows:** install [Windows Terminal](https://aka.ms/terminal) from the Microsoft Store, or use built-in PowerShell.

Then type:

```bash
ssh-keygen -t ed25519 -C "you@your-email.com"
```

(The email is just a label. No email is sent.) When prompted:

- Press Enter to accept the default file location.
- Type a passphrase you'll remember (protects the key if your laptop is stolen). Press Enter.
- Type the passphrase again. Press Enter.

Read the public key:

```bash
cat ~/.ssh/id_ed25519.pub
```

That prints a long line starting with `ssh-ed25519 AAAA...`. Copy the entire line. Add it to your VPS provider's SSH-key configuration (each provider has a section for this in their console). Now your server (when you create it, or after re-imaging it) accepts logins from your laptop.

If you're stuck on this step, search "[your VPS provider] add SSH key" — every provider has documentation for it.

### Step 3 — Connect to your server

Open a terminal on your laptop:

```bash
ssh root@203.0.113.42
```

(Replace `203.0.113.42` with the IP address of your server.)

The first time, you'll see a prompt asking if you trust the host. Type `yes` and press Enter. Enter your SSH key passphrase if asked. You should see something like:

```
Welcome to Ubuntu 24.04.x LTS ...
root@your-server:~#
```

That's the **server's** terminal prompt. Anything you type now runs on the server, not your laptop. **You're in.**

If `Permission denied (publickey)` — your SSH key isn't attached to the server. Re-check your provider's SSH key configuration.

Now jump to [Step 4 — Install Moimio](#step-4--install-moimio).

---

## Path B — Self-host with Cloudflare Tunnel

For this path, you need a computer that can stay on continuously: a desktop, a mini-PC, an old laptop you don't use any more, or a Raspberry Pi 4 (4 GB or 8 GB). You'll also need a stable internet connection at that computer's location.

### Step 1 — Prepare your computer

Install **Linux** if you haven't already:

- **Old laptop or desktop:** Ubuntu Desktop 24.04 LTS is the friendliest choice. Download from <https://ubuntu.com/download/desktop>, follow their install guide.
- **Raspberry Pi:** Use Raspberry Pi OS or Ubuntu Server for ARM. Their respective documentation covers the setup.
- **Mini-PC bought specifically for this:** Most ship with Windows, but Ubuntu installs cleanly. The Raspberry Pi imager and Ubuntu installer are both well-documented.

You don't *have* to use Linux — Moimio also runs on macOS via Docker Desktop, and on Windows via Docker Desktop with WSL2 — but for a server that stays on for months, Linux is the most predictable choice.

### Step 2 — Install Docker

Open a terminal on the computer (not via SSH from somewhere else — directly on the machine, or via SSH from a laptop on the same network if you've enabled it). Then:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Log out and back in (or restart) so the new group membership takes effect. Then verify:

```bash
docker --version
docker run --rm hello-world
```

If "Hello from Docker!" appears, Docker is working.

### Step 3 — Set up Cloudflare Tunnel

A **Cloudflare Tunnel** is a free service that gives your home/office computer a public URL without you having to open ports on your router or know your home IP. The traffic goes through Cloudflare's network, who handle TLS for you.

1. Sign up at <https://dash.cloudflare.com/sign-up> if you don't have a Cloudflare account. The free tier is enough.
2. Add your domain to Cloudflare (you'll need a domain name — see [the domain section](#getting-a-domain-name) below if you don't have one yet).
3. Go to **Zero Trust → Networks → Tunnels** in the Cloudflare dashboard. Click **Create a tunnel**, give it a name (e.g. "moimio-home"), and follow Cloudflare's instructions to install the connector on your Linux machine. Cloudflare's setup wizard provides the exact `cloudflared` install command for your OS.
4. In the tunnel's **Public hostnames** section, add a hostname like `events.yourchurch.org` and set the **Service** to `HTTP://localhost:6120`.
5. Save. Cloudflare automatically obtains and renews a TLS certificate.

Visit `https://events.yourchurch.org` in any browser — once Moimio is running on the next step, you'll reach it through the tunnel with HTTPS already configured.

For up-to-date instructions: <https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/>

### When self-hosting goes wrong

Things that go wrong with self-hosted setups during a real event, in roughly order of likelihood:

- **Power outage** at your venue or office takes the server down. Mitigate with a UPS (uninterruptible power supply, ~€80) for the computer and your router.
- **Internet outage** at your venue or office takes the public URL down. Mitigate with a mobile-tether backup ready to swap onto, or accept the downtime risk.
- **The cloudflared connector dies.** A system update, a memory spike, or a connector version drift can disconnect the tunnel without warning. Fix is typically `sudo systemctl restart cloudflared` from the host — easy *if* you can reach the host and know the command.
- **The host OS itself becomes unresponsive.** Less likely on a fresh Ubuntu install, more likely on a Raspberry Pi running other workloads or on a host that hasn't been rebooted for months. Recovery usually requires physical access.

None of these are exotic — they're the normal failure modes of running a server somewhere that isn't a data centre. The question is whether you have someone who can fix them at event time. If yes, self-hosting is a reasonable trade for keeping data physically on your premises. If no, [moimio.app](https://moimio.app) absorbs all four failure modes.

Now jump to [Step 4 — Install Moimio](#step-4--install-moimio).

---

## Step 4 — Install Moimio

This is the same regardless of whether you went VPS or self-hosted. The terminal you're in is either a VPS over SSH (Path A) or your own machine (Path B). From here on, **"the server"** means whichever computer Moimio is running on.

### 4.1 Get the code

```bash
git clone https://github.com/jc-universe87/moimio.git
cd moimio
```

`git` is preinstalled on Ubuntu. The clone takes a few seconds.

The prompt now shows you're inside the `moimio` folder.

### 4.2 Configure Moimio

```bash
cp .env.example .env
nano .env
```

`nano` is a simple text editor. Use the arrow keys to navigate. Find these lines and edit them:

**`SECRET_KEY`** — replace the placeholder with a real random string. To generate one, in a **second terminal** on your laptop:

```bash
openssl rand -hex 64
```

Copy the output. Paste as the new `SECRET_KEY` value in `nano`.

**`POSTGRES_PASSWORD`** — replace `moimio_dev` with another random string (run `openssl rand -hex 32` for a shorter one).

**`DATABASE_URL`** — find the password segment (it currently says `moimio_dev`) and replace it with the same new password you set in `POSTGRES_PASSWORD`. The two must match.

Save: **Ctrl-O**, then **Enter**. Quit: **Ctrl-X**.

### 4.3 Start Moimio

```bash
docker compose up -d --build
```

Docker downloads the base images, builds Moimio's images, and starts three containers (database, backend, frontend). First run takes **5–10 minutes**.

When it finishes:

```bash
docker compose logs --tail=30 backend
```

Look for:

```
INFO  [alembic.runtime.migration] Running upgrade ... → <latest migration>
INFO  Application startup complete.
```

If you see those, Moimio is up. **Don't proceed if you see error lines** — see the troubleshooting section at the bottom of this guide.

### 4.4 First-time setup (create your admin account)

<p align="center">
  <img src="../assets/first-time-setup.png" alt="First-time setup wizard for the initial Super Admin account" width="420">
  <br>
  <em>First-time setup wizard for the initial Super Admin account</em>
</p>

Open a browser:

- **Path A (VPS):** go to `http://YOUR_SERVER_IP:6120` (e.g. `http://203.0.113.42:6120`).
- **Path B (self-hosted):** go to `http://localhost:6120` if you're on the same machine, or `https://events.yourchurch.org` if your Cloudflare Tunnel is configured.

You'll automatically land on a **first-time setup screen** — Moimio detects that no users exist yet and offers a wizard:

- **Email** — your login.
- **Full name** — display name in the admin UI.
- **Password** — minimum 8 characters. Use a real password manager.

Submit. Your account is created with the **Super Admin** role and you're logged in.

🎉 **You've installed Moimio.**

You should land on the events list — empty for now. Click **+ New event** to create your first event.

---

## Step 5 — Make it reachable on a real domain (optional, recommended)

Visiting Moimio at `http://203.0.113.42:6120` works for you, but it's not where you'd send participants. For real registrations, you want something like `https://events.yourchurch.org`.

If you went **Path B (self-host with Cloudflare Tunnel)**, you've already done this — your tunnel URL is the public address. Skip this section.

If you went **Path A (VPS)**, continue:

### Getting a domain name

If you don't already have one, buy one from any domain registrar (Namecheap, Porkbun, INWX, Cloudflare Registrar, OVH — all fine). A `.org` domain costs about €10–15 a year.

You don't need a separate domain — a subdomain of one you already own works fine. If your church is at `yourchurch.org`, a subdomain like `events.yourchurch.org` is cleaner than a whole new domain.

If domain registration and DNS feel intimidating, this is a good moment to ask a more technically-inclined friend, or paste your situation into ChatGPT or Claude — these assistants can walk you through the specific registrar's flow in a few minutes.

### Pointing the domain at your server (VPS path)

In your registrar's DNS settings, add an **A record**:

| Name | Type | Value |
|---|---|---|
| `events` (or whatever subdomain) | A | `203.0.113.42` (your server IP) |

Save. DNS propagates in a few minutes (sometimes up to an hour). Test:

```bash
ping events.yourchurch.org
```

Replies from your server's IP = DNS is working.

### Adding HTTPS (TLS)

You have two clean options. Both work; pick whichever fits your comfort level.

#### Option 1 — Cloudflare in front

The simplest if you're new to TLS: use Cloudflare as a reverse proxy.

1. Add your domain to a (free) Cloudflare account.
2. Set the A record (or use Cloudflare Tunnel as in Path B).
3. Cloudflare automatically handles HTTPS termination — you visit `https://events.yourchurch.org` and Cloudflare proxies to your origin.

This is what many self-hosters end up doing because it's effectively "set it and forget it."

#### Option 2 — Caddy on the host

Install Caddy alongside Moimio on the same server. Caddy fetches a Let's Encrypt certificate automatically.

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

Edit `/etc/caddy/Caddyfile`:

```bash
sudo nano /etc/caddy/Caddyfile
```

Replace its contents with:

```
events.yourchurch.org {
    reverse_proxy localhost:6120
}
```

(Replace with your actual domain.) Save (Ctrl-O, Enter), exit (Ctrl-X). Reload Caddy:

```bash
sudo systemctl reload caddy
```

Caddy fetches a TLS certificate from Let's Encrypt automatically (30–60 seconds the first time). Visit `https://events.yourchurch.org`.

You can now (and should) close port 6120 from the public internet — only Caddy on the host needs to talk to it. On a Hetzner / DigitalOcean / etc. firewall, restrict 6120 to localhost. With `ufw`: `sudo ufw deny 6120`.

---

## Updating Moimio

When a new version is released, on the server:

```bash
cd ~/moimio
git pull
docker compose build --no-cache && docker compose up -d --force-recreate
```

The first command moves into the Moimio folder. The second downloads new code. The third rebuilds the images and restarts the containers.

Updates typically take 3–5 minutes. The site is briefly unavailable during the restart (10–30 seconds). If you have an event in progress, do this outside event hours.

Database migrations run automatically on backend startup — your participant data is preserved across updates.

---

## Backups

The simplest backup is a database dump. On the server:

```bash
cd ~/moimio
docker compose exec -T db pg_dump -U moimio moimio | gzip > ~/moimio-backup-$(date +%F).sql.gz
```

This creates a timestamped backup file in your home directory. Copy it to your laptop or cloud storage regularly.

To restore from a backup:

```bash
gunzip -c moimio-backup-2026-04-28.sql.gz | docker compose exec -T db psql -U moimio moimio
```

For real production deployments, automate the backup with `cron` and ship the file off-server. If that's beyond comfort, ask a technically-inclined friend, or open an issue on GitHub asking for a "scheduled-backup" guide.

---

## Troubleshooting

**`docker compose up` fails with "permission denied".**
You're not in the `docker` group. Either log out and back in (the install adds your user to the group, but only after a re-login), or use `sudo docker compose up -d --build`.

**The browser shows "this site can't be reached".**
Three checks, in order:
1. Is the server actually running? On a VPS, check the provider's console. On self-hosted, the computer needs to be on and connected.
2. Is Moimio actually running? On the server: `docker compose ps`. All three rows (db, backend, frontend) should show `Up`. If not, `docker compose logs <service>` shows why.
3. Is the firewall blocking you? VPS providers often have a separate firewall layer; make sure the port you need is open.

**The browser loads but I can't log in (and there's no first-time setup screen).**
A user already exists. The setup wizard only appears when there are zero users. Use the login form instead. If you don't know the password, reset it directly in the database — or recreate the deployment with a fresh database (only safe if there's no real data yet).

**Cloudflare Tunnel isn't reaching Moimio.**
On the server: `cloudflared tunnel run` shows live logs. Common cause: the tunnel is pointed at `localhost:80` but Moimio is on `localhost:6120`. Update the tunnel's public hostname configuration.

**HTTPS errors after setting up the domain (Caddy path).**
DNS may not have propagated yet. Wait 5 minutes and retry. Or Caddy hasn't fetched the certificate — `sudo systemctl status caddy` shows what it's doing. Logs in `journalctl -u caddy`.

**Anything weirder than that.**
Open a [bug report](https://github.com/jc-universe87/moimio/issues/new?template=bug_report.md). Include:
- What you were trying to do.
- What you actually saw (the exact error message).
- What `docker compose logs --tail=50 backend` shows.
- Mask any participant data before pasting.

---

## What's next

You have Moimio installed. To actually run an event, the [User Manual](../manual/README.md) walks through creating an event, configuring registration, running the allocation engine, doing check-in, and exporting rosters.

If you got this far without a developer's help, you've done something most people would say was "too technical for me". Welcome to self-hosted software.
