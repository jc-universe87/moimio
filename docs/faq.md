# Frequently Asked Questions

A practical FAQ for organisers, sysadmins, and curious visitors. For terminology, see the [Glossary](glossary.md).

> This FAQ covers the open-source **Moimio CE (Community Edition)** that you can self-host. A managed hosted version of the same product is available at [moimio.app](https://moimio.app); both editions share the same code and feature set.

---

## About Moimio

### What is Moimio for?

Moimio is for the moment when registrations have closed and you're staring at a spreadsheet trying to work out who sleeps where, who's on which team, and who's in which workshop — for a church retreat, a mission conference, a youth weekend, or anything similar.

It takes the registrations and proposes an allocation: rooms, small groups, teams, tables. You can accept it, change it by hand, or re-run with different settings. Then you check people in on the day and print rosters as PDFs.

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

Admins have a **Backup** page that downloads one file per event holding everything about it: participants and their answers, group types and groups, marks, placements and exclusions, the settings you chose, notes, check-in columns and ticks, and the event's history. Download one before any big change. **Restore from backup** on the same page brings an event back, on this server or a new one. The one thing a backup doesn't carry is your team's accounts; you invite them again.

To move every event at once, for example to a new server, see [Moving a workspace to your own Moimio](moving-a-workspace.md).

You're also welcome to back up the whole database with whatever tooling you already use; the installation guides show a one-line database backup. The upgrade script (`./upgrade.sh`) also takes one automatically before every upgrade.

### How do I update to a new version?

On a server installed with `git clone`, run `./upgrade.sh` from the Moimio folder. It backs up your settings and database first, then fetches and starts the new version. See [Updating Moimio](installation/beginner.md#updating-moimio) in the beginner guide.

---

## Data and privacy

### What about GDPR?

Moimio is built for European organisers, with GDPR as a first-class design concern. The short version:

- **No third-party processors.** Self-hosted means your data never leaves your deployment.
- **Data export.** A single click exports everything Moimio holds about a participant in a structured JSON file — exactly what GDPR Article 20 requires.
- **Right to erasure.** Soft delete is the standard, one-click action — the participant disappears from the People table, the engine, reports, and rosters. For the rare case where regulatory context demands full physical removal of the underlying record, that's currently a manual database operation (a first-class UI is on the post-1.0 backlog).
- **Minimal personal data in logs.** At the default log level (`LOG_LEVEL=INFO`), email addresses appear in a small number of operational lines (failed-login attempts, SMTP send/skip events) where they're needed for diagnostics, but not names, addresses, or other registration data. The `DEBUG` level does log participant data, so keep it for troubleshooting with invented data.
- **Consent-by-design.** Every registration form requires a GDPR consent tick.
- **Your own privacy notice.** A Super Admin can enter your organisation's privacy notice address under **Workspace**; the registration form then links to it right after the consent sentence.

Full details in [GDPR Compliance](gdpr-compliance.md).

### Where does the data go?

Nowhere. There is no Moimio cloud server. There is no analytics. There are no calls to external APIs during registration or allocation. Your participants' data sits in a PostgreSQL database on your server. The only things that leave it are the emails you send through your own SMTP provider and any webhooks you choose to set up.

If you self-host on a third-party VPS (Hetzner, Contabo, etc.), then that VPS provider is technically a sub-processor and you should sign a Data Processing Agreement with them — but Moimio itself does not transmit data anywhere.

### What about email — does that go through Moimio?

No. Moimio sends emails (registration confirmations, password resets) through whatever SMTP server *you* configure. The product has no email-sending capability of its own.

If you don't configure SMTP, Moimio simply doesn't send email — the app continues to work; admins manually communicate with participants.

---

## Features

### How does the allocation engine work?

It works through one group type at a time (for example Room Allocation), in a fixed order:

1. **Group codes** — people who share a group code (families, friend groups) are placed together.
2. **Marks, in the order you set** — each mark does what you chose for it: **Keep together** (e.g. all leaders in one room) or **Spread evenly** (e.g. one leader per room).
3. **Restricted groups** — groups limited to one gender (or to one mark) are filled with the people who fit them.
4. **Everyone else** — placed one by one across the remaining groups, keeping the same gender together if you leave that setting on.
5. **Tidy-up** — group sizes are evened out (optional, never breaking the rules above), leftover seats are filled, and anyone who still couldn't be placed is listed with a plain reason.

People you've **excluded** from a group type are left out of it entirely. The engine settings panel lists the switches in the same order the engine applies them.

Full detail (with the by-design imbalance trade-offs) is in [Manual section 6: Allocation Engine](manual/06-allocation-engine.md).

### What if I disagree with the engine's allocation?

A few options, roughly in increasing order of intervention:

- **Adjust settings, then re-run.** Change the engine settings (mark order, what each mark does, whether group codes are kept together, and so on) or a group's capacity or gender setting, then click **Auto-Allocate** again. The engine is deterministic — same inputs produce same outputs. **Reallocate everyone from scratch** gives you a fresh proposal that reflects the changed settings. Nothing is saved until you click **Commit allocation**.
- **Place a few people yourself, then fill in the rest.** Drag the people whose placement you care about into the right group, then click Auto-Allocate with **Allocate new participants only**. That mode keeps every existing assignment and only places people who aren't allocated yet. To protect a whole group from future runs, mark it **Keep as-is**.
- **Keep someone out.** **Exclude** a person from one group type (say, the room draw) and they stay in every other group type.
- **Manual changes only.** Drag participants between groups on the board and skip re-running entirely. The engine proposes; you decide.

### Can I run Moimio without using the engine at all?

Yes. Skip the engine and place every participant by hand. Group types and groups work fine without it — the engine is an accelerator, not a requirement. If you don't need allocation at all (registration only), a self-hoster can switch it off with `FEATURE_ALLOCATION=false` in `.env`.

### How does the family / friend group feature work?

When registering, a person can enter a **group code** — typically a surname plus a number (e.g. `SMITH-742`). Everyone registering with the same group code is kept together by the engine, in every group type where **Keep group codes together** is switched on (it is by default). People added on the same form can simply tick that they share the main registrant's code.

If a registrant doesn't enter a group code, Moimio auto-generates one (`STEM-NNN` — a stem derived from the surname, plus a unique three-digit suffix, e.g. `SMITH-742`) and includes it in the registration confirmation email so the registrant can share it with anyone else who'd like to be grouped with them. The suffix is unique within the event — two unrelated families both auto-generated as `SMITH-...` get different suffixes and don't accidentally cluster together.

### What's a "mark"?

A coloured label that staff can attach to participants — "leader", "first-timer", "needs ground floor", "vegetarian", anything you find useful. Each mark can influence allocation, separately in each group type: **Keep together** (e.g. all leaders in one room), **Spread evenly** (e.g. one leader per room), or **No effect** (it's just a visual label). A group can also be reserved for people with one mark.

Marks are for your team only — participants never see them.

### Can I integrate Moimio with Slack, Zapier, or my own systems?

Yes, through webhooks. Moimio CE can send a signed HTTP message to addresses you configure when certain things happen. Today those are: an event is created, an event is deleted, and an allocation is committed. Configure endpoints under **Webhooks** in the sidebar (Super Admin only). Each message is signed with HMAC-SHA256 using a per-endpoint secret you receive on creation, so your receiver can check it really came from Moimio.

Common use cases:

- A Slack channel message whenever a new event is created
- A Zapier or n8n flow that kicks off when an allocation is committed
- A custom script that keeps another system in step with your events
- Anything else that accepts inbound HTTP webhooks

There is no webhook for individual registrations yet.

Full integration guide with code samples: [docs/webhooks.md](webhooks.md).

The feature is optional; nothing is sent until you add an endpoint. For safety, addresses on private networks (`192.168.x.x`, `10.x.x.x`, `localhost` and similar) are refused; if your receiver really is on your own network, set `WEBHOOK_ALLOW_PRIVATE_TARGETS=true` in `.env`. To hide the feature entirely, set `FEATURE_OUTBOUND_WEBHOOKS=false`.

---

## Languages and localisation

### Which languages does Moimio support?

The user interface is fully translated into 6 languages with key parity:

- English
- German (Deutsch)
- Korean (한국어)
- Spanish (Español)
- Brazilian Portuguese (Português (Brasil))
- French (Français)

Participants and staff each pick their own preferred language; the admin language and the registration form language are independent. The two built-in group types (Room Allocation and Small Groups) follow each reader's language until you rename them. Printed rosters have their own language choice, so you can print an English roster from a German screen.

### Can I add my own language?

Yes. Each language is one JSON file of interface text, plus a line in the app's list of languages; the app is then rebuilt. See [TRANSLATION_RULE.md](../TRANSLATION_RULE.md) for the contributor workflow. Open an issue first to confirm the locale code we'll add.

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
