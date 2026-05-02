# Changelog

All notable changes to Moimio CE are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This is the public, user-facing changelog. Detailed per-development-iteration history is kept internally and is not published.

---

## [Unreleased]

Nothing yet. Open issues at <https://github.com/jc-universe87/moimio/issues> for things you'd like to see.

---

## [1.0.0] — 2026-05-02

Initial public release of **Moimio CE (Community Edition)**. Moimio reaches feature-completeness for the small and mid-sized event use case it was designed for: church, mission, and retreat organisers.

### Added

- **Events.** Create, configure, and run events end-to-end. Lifecycle: draft → open → closed, with a separate archive flag for long-term storage.
- **Public registration form** with per-event field configuration. Six toggleable built-in fields (gender, date of birth, phone, address, country, church/organisation) plus custom fields (text, number, select, boolean, date) backed by an EAV schema so each event has its own form shape.
- **Group codes.** Family or friend groups register together using a shared code (e.g. `SMITH-742`); the engine keeps them together at allocation time. Auto-generated server-side if a registrant doesn't enter one, and included in the registration confirmation email so they can share it with others.
- **Marks.** Colour-coded badges for staff-visible tagging — "leader", "first-timer", "needs ground floor", anything an organiser wants to track. Marks influence the allocation engine via configurable per-mark behaviour (keep together, spread evenly, no effect).
- **Allocation engine.** A deterministic 5-pass algorithm that proposes a full allocation in one shot — respecting group-code clusters, mark behaviours, gender restrictions, and capacities. Two modes: top-up (keep existing assignments and place new participants only) or replace (reallocate everyone from scratch). Admins can commit, override, or re-run with adjusted settings.
- **Allocation categories and units.** Generic system replacing per-type tables: define your own categories (with `exclusive` — one unit per participant — or `overlapping` — many units per participant — rules). New events come pre-seeded with **Rooms** and **Small Groups** as defaults.
- **Check-in.** Custom tick columns per event ("Arrived", "Welcome pack", "Payment"); immersive check-in mode for tablet/phone use at the door; multiple staff can check in concurrently.
- **PDF roster exports.** Compact and Sign-in formats. CJK-safe (Korean rosters render correctly using Noto Sans CJK).
- **CSV imports and exports.** Batch participant registration from a spreadsheet; CSV export of the full participant list with allocations and custom fields.
- **GDPR data export.** Per-participant JSON export covering every record Moimio holds about that person — built for fulfilling Article 20 (data portability) and Article 15 (right of access).
- **Data backup and restore.** Full event archive download and restore for migrations between deployments. Two backup modes: full or structure-only (GDPR-safe template sharing).
- **Multi-language UI.** English, German, Korean, Spanish, Brazilian Portuguese, French — 6 locales with full string parity.
- **Notes.** Note system — staff can attach private or shared notes to participants. The `is_published` flag controls whether other staff see them.
- **Staff permissions.** Per-event assignment with five permission surfaces — People (read/write/none), Organise (read/write/none), Marks (write/none), Check-in (write/none), Reports (read/none).
- **Self-hosting.** One `docker compose up` away. No external services required. SMTP optional.

### Notes

- Moimio CE v1.0 is the first public release. Earlier versions were internal development iterations and are not published.
- For the technical specification of the allocation engine, see the module docstring at `backend/app/services/engine_service.py`.
- Moimio CE's code and documentation were substantially developed with [Claude Opus 4.7 Adaptive](https://www.anthropic.com/claude).

---

## Versioning policy

- **Major version** (`x.0.0`) — breaking schema or API changes that require migration steps beyond `alembic upgrade head`.
- **Minor version** (`1.x.0`) — new features, backwards-compatible.
- **Patch version** (`1.0.x`) — bug fixes, translation updates, dependency bumps.

Pre-release tags use a suffix: `1.1.0-rc.1`.
