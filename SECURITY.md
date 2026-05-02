# Security Policy

Thank you for helping keep Moimio CE and its users safe.

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

The preferred channel is **[GitHub's private vulnerability reporting](https://github.com/jc-universe87/moimio/security/advisories/new)**. This is a private, two-way conversation between you and the maintainers, hosted by GitHub. To submit a report:

1. Go to the [Security tab](https://github.com/jc-universe87/moimio/security) of the Moimio repository.
2. Click **Report a vulnerability**.
3. Fill in the form with as much detail as you can.

If you don't have a GitHub account, or if GitHub's reporting form is unavailable, you can email:

**`contact@moimio.app`**

(Use the GitHub channel where possible — it's encrypted in transit, keeps the discussion threaded, and avoids inbox-side risks.)

## What to include

A useful report contains:

- **A description** of the vulnerability and its potential impact.
- **Reproduction steps** — exact requests, payloads, or conditions that trigger the issue.
- **The affected version(s).** A git SHA or a release tag is ideal.
- **Any proof-of-concept code or screenshots** you've already produced.
- **Your environment** — browser, OS, deployment topology (self-hosted on what kind of host, behind what reverse proxy, etc.).

## What you can expect from us

Moimio CE is maintained by one person in spare time. We will:

- Acknowledge your report and work with you to understand and reproduce the issue.
- Assess severity and respond with our planned approach.
- Develop, test, and release a fix as quickly as the issue's severity warrants and our maintainer time allows.
- Coordinate public disclosure with you once a fix is available.

We deliberately don't publish fixed timelines for these stages. Single-maintainer projects can't honestly commit to fixed SLAs, and we'd rather work through reports thoroughly than rush to hit a number. We'll keep you informed at each step.

If we determine the report is not a security issue (for example, the behaviour is intentional or the impact is below threshold), we'll explain why.

## Disclosure policy

We follow **coordinated disclosure**:

- We work with you to understand and reproduce the issue.
- We develop and test a fix.
- We release the fix (typically as a patch version, e.g. `1.0.x`).
- We publish a [GitHub Security Advisory](https://github.com/jc-universe87/moimio/security/advisories) crediting the reporter (unless you ask to remain anonymous).

Please do not publicly disclose the issue until a fix has been released and the advisory is published. We aim to keep the embargo period as short as possible.

## Scope

### In scope

- The Moimio backend (`backend/`) and frontend (`frontend/`) source code in this repository.
- The default Docker Compose deployment topology.
- Authentication, authorisation, session handling, and CSRF/XSS surfaces.
- Personal data handling — anything that could expose participant data beyond its intended audience.
- Privilege escalation between user roles (super_admin / staff) or between events.
- Allocation engine determinism and integrity (engine output that violates documented hard constraints).

### Out of scope

- Vulnerabilities in third-party dependencies. Please report those upstream first; if a Moimio mitigation is needed, link the upstream report when filing here.
- Issues in self-hosters' own infrastructure (their VPS, their reverse proxy, their TLS configuration).
- Findings from automated scanners with no demonstrated exploit (please reproduce by hand before reporting).
- Best-practice deviations that don't have a concrete impact (e.g. "this header could be stricter" without an attack scenario).
- Social-engineering, physical-access, or denial-of-service attacks against the project's own infrastructure.

## Supported versions

| Version | Supported |
|---|---|
| `1.0.x` (latest) | ✅ Security fixes |
| Pre-`1.0.x` | ❌ No support — these were internal development iterations |

We will support the latest minor release line and the previous one, once a `1.1` exists.

## Recognition

Security researchers who report valid issues will be credited in the corresponding GitHub Security Advisory and in the [CHANGELOG](CHANGELOG.md), unless they prefer to remain anonymous. We do not currently have a paid bug bounty programme.

## Hardening recommendations for self-hosters

These are not vulnerabilities in Moimio itself, but they materially affect the security posture of a deployment:

- **Set a strong `SECRET_KEY`** in your `.env`. The `.env.example` placeholder is *not* safe for production. Use a 64+ character random string.
- **Change the default database password** (`POSTGRES_PASSWORD=moimio_dev`).
- **Run behind HTTPS.** Caddy is the recommended frontend; pair with a TLS-terminating reverse proxy if you're behind one.
- **Restrict the database port** (`6122`) to localhost in production. Don't expose Postgres to the public internet.
- **Keep your Docker host patched.** Moimio's containers are only as secure as the kernel underneath them.
- **Configure SMTP credentials carefully.** Use app-specific passwords, not your main account password.
- **Review your registration form fields.** Don't collect personal data you don't need — GDPR data minimisation applies to your event, not just to Moimio.

Thank you for helping us keep Moimio safe for the people who depend on it.
