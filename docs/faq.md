# Frequently Asked Questions

A practical FAQ for organisers, sysadmins, and curious visitors. For terminology, see the [Glossary](glossary.md).

> This FAQ covers the open-source **Moimio CE (Community Edition)** that you can self-host. A managed hosted version of the same product is available at [moimio.app](https://moimio.app); both editions share the same code and feature set.

---

## About Moimio

### What is Moimio for?

Moimio is for the moment when registrations have closed and you're staring at a spreadsheet trying to work out who sleeps where, who's on which team, and who's in which workshop — for a church retreat, a mission conference, a youth weekend, or anything similar.

It takes the registrations and proposes an allocation: rooms, groups, teams. You can accept it, override it, or re-run with different settings. Then you check people in on the day and export rosters as PDFs.

### Who is Moimio for?

Volunteer-run organisers of small-to-medium events — typically up to about 300 participants. Churches, mission organisations, youth ministries, retreat centres, conference hosts.

It's *not* designed as enterprise event tooling, ticketing infrastructure, or a public events marketplace. If you need one of those, Moimio is the wrong fit and we'd rather tell you upfront.

### Is it really free?

Yes. The MIT licence means you can self-host Moimio forever, with no fees, no usage limits, and no obligation to share what you build with it.

A paid managed-hosting option is available under https://moimio.app for organisations that want the product without running their own infrastructure. The self-hosted edition will always remain free and full-featured.

### Do I need to know how to code to use Moimio?

To **use** Moimio (after it's installed): no. The admin interface is point-and-click, the same way you'd use any other web app.

To **install** Moimio: it depends on your comfort level. The fastest install is `docker compose up -d --build`, which assumes you can open a terminal. If that's intimidating, the [Beginner Installation Guide](installation/beginner.md) walks through the process step by step. If even that feels like too much, ask a technically-inclined friend at your church — Moimio is built on standard tools (Docker, PostgreSQL, FastAPI, React), so anyone with hobby-grade sysadmin experience can get it running in an afternoon.

### Why is it called Moimio?

**모임이오** is a Korean phrase meaning "It is a gathering!" — a small declaration that affirms the moment when a group has come together. The romanisation drops the hyphens for a one-word, pronounceable name.

The English tagline **Gather · Organise** captures the same thing: people come together, then we make sense of how they're organised.

---

## Hosting and infrastructure

### Where can I host Moimio?

Anywhere that runs Docker. It is intended to work on:

- A laptop or office desktop, for very small events.
- A Raspberry Pi 4 or similar single-board computer.
- A church-owned mini PC (the kind sold for under €200).
- A €5/month VPS at Hetzner, Contabo, or similar.
- Any cloud provider with a small Linux VM.

It does *not* require a Kubernetes cluster, a load balancer, or any cloud-managed services. By design.

### Does it need to be online?

For the admin interface and check-in, you can run Moimio entirely on a local network — useful for retreat centres with patchy internet. For public registration (participants signing up from home), the server needs to be reachable from the internet.

A common pattern: run Moimio on a local mini-PC, expose it temporarily through a service like Cloudflare Tunnel during the registration window, then take it offline once registration closes.

### Will it scale to 1000 participants? 5000?

Moimio is currently tuned for **small and mid-sized events** — roughly speaking, the kind of retreat, conference, or camp where the organising team knows most of the participants by name, and where one or two organisers can hold the event in their head.

The architecture has no fundamental ceiling — PostgreSQL, FastAPI, and React all scale to far larger workloads — but specific parts of the product (the AllocationBoard's at-a-glance density, the allocation engine's pass strategy, the bulk-operations UX) are designed for the small/mid range and haven't been optimised for higher scale yet. Performance work for larger events is on the roadmap, but isn't a current priority.

If you're running a 1000+ person event today, Moimio will technically function, but you'll feel the design tension. You may be better served by event-management tools built for that scale.

### What if I lose my server?

Moimio includes a full-event backup feature: a single archive containing every record for an event (participants, allocations, custom fields, marks, notes, check-in state). Download it before any major operation; restore it on a fresh deployment if you need to.

You're also welcome to back up the underlying PostgreSQL volume with whatever tooling you already use — Moimio's data lives in standard tables and is portable.

---

## Data and privacy

### What about GDPR?

Moimio is built for European organisers, with GDPR as a first-class design concern. The short version:

- **No third-party processors.** Self-hosted means your data never leaves your deployment.
- **Data export.** A single click exports everything Moimio holds about a participant in a structured JSON file — exactly what GDPR Article 20 requires.
- **Right to erasure.** Soft delete is the standard, one-click action — the participant disappears from the People table, the engine, reports, and rosters. For the rare case where regulatory context demands full physical removal of the underlying record, that's currently a manual database operation (a first-class UI is on the post-1.0 backlog).
- **Minimal PII in logs.** Logs avoid rich personal data; email addresses appear in a small number of operational lines (failed-login attempts, SMTP send/skip events) where they're load-bearing for diagnostics, but not names, addresses, or other registration data.
- **Consent-by-design.** Every registration form requires a GDPR consent tick.

Full details in [GDPR Compliance](gdpr-compliance.md).

### Where does the data go?

Nowhere. There is no Moimio cloud server. There is no analytics. There are no calls to external APIs during registration or allocation. Your participants' data sits in a PostgreSQL database on your server, full stop.

If you self-host on a third-party VPS (Hetzner, Contabo, etc.), then that VPS provider is technically a sub-processor and you should sign a Data Processing Agreement with them — but Moimio itself does not transmit data anywhere.

### What about email — does that go through Moimio?

No. Moimio sends emails (registration confirmations, password resets) through whatever SMTP server *you* configure. The product has no email-sending capability of its own.

If you don't configure SMTP, Moimio simply doesn't send email — the app continues to work; admins manually communicate with participants.

---

## Features

### How does the allocation engine work?

It runs five passes over your participants:

1. **Group-code clusters** — keeps families and friend groups together.
2. **Mark "together" clusters** — keeps people sharing a tag together (e.g. all leaders in one room).
3. **Mark "split-evenly" pre-distribution** — spreads people sharing a tag evenly (e.g. one leader per room).
4. **Drain gender-restricted units, then round-robin the rest.**
5. **Classify anyone unplaced** with a clear reason.

Full detail (with the by-design imbalance trade-offs) is in [Manual section 6: Allocation Engine](manual/06-allocation-engine.md).

### What if I disagree with the engine's allocation?

Three paths, in increasing order of intervention:

- **Adjust settings, then re-run.** Tweak mark priorities, mark behaviours, gender restrictions, or unit capacities, then click Auto-Allocate again. The engine is deterministic — same inputs produce same outputs. By default the re-run uses "Reallocate everyone from scratch", which gives you a fresh proposal that incorporates the changed settings.
- **Drag the specific participants you want to fix, then re-run with "Allocate new participants only".** Manually drop the people whose placement you care about into the right unit — those manual placements lock — then click Auto-Allocate with the **Allocate new participants only** mode. The engine fills around your manual fixes without disturbing them. This is the most surgical path when you want most of the engine's proposal but with a few specific exceptions.
- **Manual override only.** Drag participants between units in the AllocationBoard and skip re-running entirely. The engine doesn't lock you out; it proposes, you decide.

### Can I run Moimio without using the engine at all?

Yes. Skip the engine and place every participant manually. The category-and-unit system works fine without the algorithm — the engine is an accelerator, not a requirement.

### How does the family / friend group feature work?

When registering, a person can enter a **group code** — typically a surname plus a number (e.g. `SMITH-742`). Anyone else registering with the same group code is part of that cluster, and the engine will try to keep them in the same room (or the same small group, depending on category).

If a registrant doesn't enter a group code, Moimio auto-generates one (`STEM-NNN` — a stem derived from the surname, plus a unique three-digit suffix, e.g. `SMITH-742`) and includes it in the registration confirmation email so the registrant can share it with anyone else who'd like to be grouped with them. The suffix is unique within the event — two unrelated families both auto-generated as `SMITH-...` get different suffixes and don't accidentally cluster together.

### What's a "mark"?

A coloured badge that staff can attach to participants — "leader", "first-timer", "needs ground floor", "vegetarian", anything you find useful. Each mark can influence allocation: you can tell the engine to **keep marked people together** (e.g. cluster all leaders in one room), or to **spread them evenly** (e.g. one leader per room), or to **ignore the mark for allocation** (it's just a visual tag).

Marks are staff-internal — participants never see them.

---

## Languages and localisation

### Which languages does Moimio support?

The user interface is fully translated into 6 languages with key parity:

- English
- German (Deutsch)
- Korean (한국어)
- Spanish (Español)
- Brazilian Portuguese (Português Brasil)
- French (Français)

Participants and staff each pick their own preferred language; the admin language and the registration form language are independent.

### Can I add my own language?

Yes. The translation system is fully external (JSON files, no compilation step). See [TRANSLATION_RULE.md](../TRANSLATION_RULE.md) for the contributor workflow. Open an issue first to confirm the locale code we'll add.

The user manual itself is currently English-only; community translations are welcome but not pre-built.

---

## Support and community

### What if I find a bug?

[Open a bug report](https://github.com/jc-universe87/moimio/issues/new?template=bug_report.md). The template asks for the information needed to reproduce.

### What if I have a feature idea?

[Open a feature request](https://github.com/jc-universe87/moimio/issues/new?template=feature_request.md). Even better: describe a real workflow that's hard or impossible today, and let the discussion shape the solution.

### Can I get paid support?

Not currently. Moimio is built and maintained by one person in spare time. If you're a church or organisation that depends on the product and wants prioritised support or feature development, [GitHub Sponsors](https://github.com/sponsors/jc-universe87) is a way to express that.

### Is there a community forum?

Not yet. GitHub Issues and Discussions are the canonical channels for now. As the user base grows, a more conversational space (Matrix, Discord, or similar) is on the table.

---

## Future

### Will there be AI features?

Possibly, opt-in only. The Phase 3 roadmap includes AI-assisted allocation suggestions (for example, asking a model to propose room assignments based on registration notes). Two things are non-negotiable:

- **Explicit opt-in per organisation.** Off by default. Turning it on requires a separate consent step distinct from registration consent.
- **Bring-your-own-API-key.** No data is sent to a Moimio-controlled AI service. You wire in your own provider key (Anthropic, Google, OpenAI, or a self-hosted local model), or you don't use the feature at all.

### Is there a managed hosting option?

Yes. **Moimio** (the hosted product) is available at [moimio.app](https://moimio.app). It runs the same code as Moimio CE — same allocation engine, same registration flow, same data model — with hosting, backups, and updates handled for you. Pick whichever edition fits your situation; Moimio CE will always be free and full-featured.
