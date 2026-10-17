# Moimio CE — Architecture and Design Principles

This document captures the **why** behind Moimio: the product shape, the architectural choices, and the design principles that decisions are filtered through. It complements rather than duplicates:

- the **[User Manual](docs/manual/README.md)** — *what* the product does, from an organiser's chair
- the **[Installation Guide](docs/installation/README.md)** — *how* to get it running
- the **[Data Model](docs/data-model.md)** — the schema in detail
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — how to send a patch

Read this when you want to understand why Moimio is the way it is — whether you're a contributor about to write a feature, an operator deciding whether the product fits your situation, or future-you returning to the codebase after a long absence.

---

## 1. The problem Moimio solves

Church and mission conference organisers face a two-stage problem.

**Registration** — collecting names, contact details, and preferences from a list of participants — is well-served by existing tools. A small church can do it with Google Forms.

**Allocation** — turning that list into rooms, small groups, and work teams while respecting families, friend groups, gender restrictions, leadership balancing, and special-needs flags — is where existing tools stop. It's overwhelmingly done by hand, in spreadsheets, late at night, with corrections messaged around at 11pm.

Moimio's reason for existing is to bridge that gap. Registration flows directly into a structured allocation pipeline; the engine proposes a full assignment in one shot; the organiser commits, overrides, or re-runs.

Without the allocation engine, Moimio collapses into a generic registration database. The engine *is* the product.

---

## 2. Product invariants

Every architectural decision is filtered through these. They are not up for negotiation on a per-feature basis.

### 2.1 Self-hostable, no required third-party services

Moimio runs as three Docker containers (backend, frontend, PostgreSQL) on anything from a Raspberry Pi to a VPS. No cloud lock-in. No required SaaS dependencies. SMTP is optional — the product still functions without email; organisers communicate manually.

A feature that introduces a hard dependency on an external service (analytics, hosted databases, paid APIs, third-party authentication) is rejected by default. If there's a strong case, the dependency must be optional and toggleable.

### 2.2 GDPR-first

Personal data stays inside the deployment. There is no Moimio cloud server in the CE edition; there is no analytics; there are no calls to external APIs during registration or allocation, other than the SMTP server and webhook endpoints the operator configures (and webhook payloads carry no participant data). Self-hosting means the organiser is the data controller and Moimio is not a sub-processor.

GDPR primitives are first-class:

- **Article 20 export** — a single click exports every record Moimio holds about a participant in a structured JSON file.
- **Article 17 erasure** — soft delete is one click; hard erasure is supported as a manual database operation (a first-class UI is post-1.0 backlog).
- **Per-event audit log** — `allocation_events` is append-only and records every assignment, removal, exclusion and re-inclusion, with nullable references so erasure does not rewrite history.
- **Structure-only backup mode** — backs up the event's *configuration* (categories, units, marks, custom fields, form layout, check-in columns) without participant data, notes, or the organiser's email sender details, for sharing event templates publicly without leaking personal data.
- **Privacy notice link** — a workspace setting (`workspace_settings.privacy_notice_url`, v1.0.6) puts the organisation's own privacy notice on the public registration form.
- **Quiet logs by default** — `LOG_LEVEL=INFO`; `DEBUG` turns on SQL query logging, which writes personal data to the log, so it is opt-in (v1.0.5).

Full detail in [docs/gdpr-compliance.md](docs/gdpr-compliance.md).

### 2.3 Volunteer-organiser-friendly, not enterprise-flexible

Moimio is built for **small and mid-sized event organisers** — churches, missions, retreats — running events of up to ~300 participants. Decisions are filtered through that lens.

A feature request that makes Moimio more enterprise-flexible at the cost of being harder to set up for a volunteer organiser is, almost always, the wrong direction. We accept lower flexibility ceilings to preserve the floor.

### 2.4 Doing obvious things well

Moimio prefers a smaller feature that's reliable over a larger feature that's clever. The allocation engine is intentionally a deterministic pass-based algorithm (five numbered passes, the fourth split into sub-steps) rather than a constraint solver or an optimisation problem — it produces the same output for the same input every time, and an organiser can read what it did and why.

---

## 3. The three-phase event lifecycle

Every event passes through three phases. The phases are not arbitrary screens — they correspond to what's safe to change at each point.

### Setup

The organiser defines structure: registration form fields, custom fields, allocation categories (Rooms, Small Groups, plus any added), units within those categories, marks, engine settings. Nothing has been published yet.

### Registration

The form is open. Participants register; the organiser confirms or cancels them; staff attach marks; group codes link related registrations. Structure is now mostly locked: changes that would invalidate prior registrations (renaming a custom field, removing a registration-form question) are restricted.

### Execution

Registration is closed (or open with allocations as a moving target). The allocation engine runs; the AllocationBoard becomes the central surface; check-in begins on arrival; rosters are exported.

The phase is implicit — there is no "switch to phase 2" button. Each surface adapts to whether the event has registrations yet, whether allocations exist, whether check-in has begun. The phase model exists to make those adaptations coherent rather than ad-hoc.

---

## 4. The allocation engine

The engine is the heart of the product. Three things to know.

### 4.1 Deterministic pass-based algorithm

Same inputs → same output, every time: participants are read in registration order (`created_at`, then id) and every ordering has a stable tie-break. Before any pass, people **excluded** from the group type are removed from the pool, and in a re-allocation the occupants of units marked **keep as-is** (`is_kept`) are frozen in place. Then, in order:

- **Pass 1 — Group-code clusters.** Families and friend groups (linked by a shared `group_code`, when `use_group_codes` is on) are placed together in the smallest unit that fits, or split evenly across the fewest units if `split_oversized_groups` allows; otherwise the whole cluster is held back as unplaced. With `exclusive_group_codes` a cluster claims its unit outright.
- **Passes 2–3 — Marks, in the group type's mark priority order.** One walk of `mark_priorities` (since v1.0.4e, so the organiser's order wins). A `together` mark packs its holders like a cluster, filling one unit at a time so at most one unit ends mixed; a `split` mark spreads its holders round-robin across eligible units.
- **Pass 4 — Fill.** (a) Drain restricted units — gender- or mark-restricted — with eligible people; (b) round-robin everyone left into unrestricted units; (c) optional **equalising sweep** (`equalise_after_allocation`, default on) moves whole movable clusters to even out occupancy; (d) a final **backfill** puts anyone still unplaced into any eligible unit with room.
- **Pass 5 — Classify anyone unplaced** with a reason tag — e.g. `cluster_oversized_split_disabled`, `cluster_no_eligible_unit`, `gender_unknown_no_mixed_unit_available`, `no_capacity_remaining`.

Hard constraints are never broken: unit gender restriction, unit mark restriction, and capacity (a capacity of `0` means no limit). Pass 1 takes precedence over passes 2–3 by design — group codes are an explicit family/friend signal; marks are a staff signal. If the two conflict, group codes win.

The full algorithm is documented in the top-of-file docstring of `backend/app/services/engine_service.py`; the equalising sweep (4c) and backfill (4d) are described in the inline comments at those passes.

### 4.2 Imbalance is by design

The engine produces a valid allocation, not the *most balanced* allocation. Capacities are respected; clusters are kept; gender restrictions are enforced. The equalising sweep evens out what it can by moving whole clusters, but it never splits a cluster or breaks a restriction, so a large family can still leave one unit visibly fuller than the rest.

This is intentional. A "perfectly balanced" output would require either ignoring clusters (defeating the point) or shuffling individuals after the fact. Organisers who want a tighter balance use a `split` mark instead of a group code, or **Reallocate everyone from scratch** with adjusted unit capacities.

### 4.3 Two modes: top-up vs replace

- **Top-up** (`Allocate new participants only`) — keep existing assignments, place unallocated participants only. Used after registration re-opens or after a manual fix the organiser wants to preserve.
- **Replace** (`Reallocate everyone from scratch`) — clear the group type and propose a fresh allocation. This is the engine's default mode.

Top-up keeps every existing placement, manual or engine-made, except that anyone who no longer meets their unit's gender or mark restriction is re-placed, and anyone now excluded is dropped. Replace discards them all, except the occupants of units marked **keep as-is**, which neither mode touches. Either way the engine only *proposes*; nothing is written until the organiser commits, and only a commit emits the `event.allocated` webhook.

### 4.4 Append-only allocation events

Every state-changing operation on the allocation pipeline writes a row to `allocation_events`. The table is append-only at the application layer (no `UPDATE`, no `DELETE`). It serves three purposes:

- **Audit.** Who placed, moved, removed, excluded or re-included whom, by which route (`source`: manual, engine commit, cancellation, exclusion, ...), and when. Engine commits carry a `run_id`; the engine settings used are not stored.
- **Reasoning surface.** When the engine places a participant, the reason — pass number, cluster ID, gender restriction match — is captured and surfaced in the InsightPanel.
- **Forensic recovery.** If something goes wrong, the history is reconstructable.

---

## 5. Generic allocation primitives

The original Phase 1 schema had three tables: `Room`, `Group`, `Team`. Phase 2 abandoned that for a single generic system.

- **`AllocationCategory`** — a named kind of allocation (e.g. "Rooms", "Small Groups", "Workshops"). Has a `rule_type`:
  - `exclusive` — one participant in only one unit (rooms, primary small groups).
  - `overlapping` — one participant in many units (sessions, workshops, shifts).
- **`AllocationUnit`** — a named slot within a category, with capacity (`0` = no limit), optional gender restriction, optional mark restriction (only holders of that mark may be placed), and a **keep as-is** flag that freezes its occupants.
- **`Allocation`** — links a participant to a unit. UNIQUE on `(participant_id, unit_id)`.
- **`AllocationCategoryExclusion`** — keeps one participant out of one category while leaving them in every other (v1.0.5). The engine honours it before any pass; a committed placement lifts it.

This generalisation is what lets organisers add their own categories ("Workshops", "Buses", "Meal shifts") without a schema change. New events come pre-seeded with two built-in types, **Room Allocation** and **Small Groups**, whose names are rendered in the reader's language (via `name_key`) until the organiser renames them; the engine has no special-casing for either.

---

## 6. Marks and group codes

Two participant-tagging primitives serve different purposes; understanding the distinction is key to using either well.

### 6.1 Marks — staff-internal colour-coded tags

Marks are coloured badges attached by staff: "leader", "first-timer", "needs ground floor", "vegetarian". They are **staff-internal** — participants never see them — and **per-event** — a mark on Event A doesn't carry to Event B.

Each mark has a default allocation behaviour (`MarkDefinition.cluster_behaviour`), which a group type can override in its mark priority list:

- `together` — cluster marked participants in the same unit.
- `split` — distribute marked participants evenly across units.
- `none` — purely visual, no engine effect.

A mark only affects a group type's allocation if it is in that group type's `mark_priorities`, and the list order decides which mark wins when a person carries several. A leader mark might be `together` for Rooms (leaders share a room) but `split` for Small Groups (one leader per group). A unit can also be restricted to holders of one mark.

### 6.2 Group codes — registration-time family/friend identifiers

A `group_code` is a string assigned at registration time (e.g. `SMITH-742`). Participants entering the same code form a cluster that the engine keeps together at allocation time.

If a registrant doesn't enter one, Moimio auto-generates `STEM-NNN` (a stem derived from the surname plus a unique three-digit suffix, scoped to the event), and includes it in the confirmation email so the registrant can share it.

A group code applies in every group type where the engine setting "keep group codes together" (`use_group_codes`) is on, which is a per-group-type switch on the allocation board. So an organiser who wants codes ignored for workshops turns that switch off for workshops.

There was once a per-person alternative: a `group_code_categories` field limiting one person's code to particular group types. It was enforced by the engine and by nothing else, no screen could ever see or set it, and it was retired in v1.0.5. Its column is unread from that release and is dropped after it.

The engine treats group-code clusters in pass 1, before any mark logic. This means group codes effectively override mark behaviours — if a married couple are both leaders and the leader mark is `split`, the engine will still keep them in the same room.

---

## 7. Person-first UI

The organiser's view is people, not containers.

The AllocationBoard shows units (rooms, groups) as containers, but the entry surface for understanding what's going on with a specific person — their preferences, their group code, their marks, their notes, why the engine placed them where it did — is the **InsightPanel**, a slide-over that opens from anywhere on the board without dismissing it.

Two design consequences:

- **The AllocationBoard never dims.** When the InsightPanel opens, the board stays at full opacity and the operator can keep working it — drag-and-drop, capacity edits, manual placement — without losing their place.
- **Participant context follows the operator.** The InsightPanel is reachable from the AllocationBoard, the People table, the CheckInPanel, and the Reports surface. The data is the same; the entry point depends on what the operator was doing.

This was a deliberate move away from the early "container-first" thinking in which the AllocationBoard was structured around rooms with people as a property of rooms. The shift produced a more accurate mental model: people are the central object; being in a room is a relationship.

---

## 8. Operator UX principles

Three principles run through the admin surface.

### 8.1 One interface for the first-timer and the tenth-timer

The operator running their first event and the operator running their tenth event use the same interface. The product does not have a "wizard mode" that's later replaced by an "advanced mode" — the same surfaces, the same controls, with sensible defaults and clearly-named settings, work for both.

This rules out hidden settings, magic auto-modes, and progressive disclosure that hides depth from beginners. It also rules out forcing a tenth-time operator through hand-holding they no longer need.

### 8.2 Mobile parity for the operating surfaces

The AllocationBoard, the People table, the CheckInPanel, and the InsightPanel all have full mobile-card render paths. Check-in at the door of a venue happens on a phone or tablet, not a laptop. The mobile experience is a parallel surface designed for one-handed use, not a degraded fallback.

### 8.3 Slide-overs over modal stacks

Slide-over panels (InsightPanel, the Sidebar) are preferred over stacked modals. A modal stack hides the operator's context; a slide-over keeps it visible. When a participant detail surface opens, the underlying board stays interactive.

---

## 9. Internationalisation

The UI is fully translated into 6 locales: English, German, Korean, Spanish, Brazilian Portuguese, French. Three things are deliberate.

**Build-time parity.** A Python script (`frontend/scripts/validate-i18n-keys.py`) gates `npm run build` and refuses any build where a static `t('key')` callsite has no matching key in the English source-of-truth dictionary. Its main catch is the dot-versus-underscore mismatch (`event.archive.confirm_title` written as `event.archive.confirm.title`), a bug that reached production twice; dynamic keys built at runtime are not checked.

**No auto-translation.** New keys must be human-translated into all six locales in the same PR. English is the source of truth; missing keys in other locales fall back to English at runtime, but parity is the contract. Auto-translation services produce locale-specific drift that's hard to detect and worse to debug.

**The brand mark stays English.** The tagline **Gather · Organise** is not translated. It is the brand mark, not a product label.

Full detail in [TRANSLATION_RULE.md](TRANSLATION_RULE.md).

---

## 10. Outbound webhooks for integrations

From v1.0.0g, Moimio CE can POST signed HTTP notifications to URLs you configure, the moment a system event happens. This is the integration seam — wire Slack notifications, Zapier flows, custom scripts, accounting systems, anything that accepts inbound webhooks.

The subsystem is a deliberate architectural commitment, not a feature add. It has three load-bearing properties:

**Generic, not deployment-specific.** Moimio CE doesn't know who's listening on the other end of a webhook. The receiver might be a self-hoster's Zapier flow, an external billing layer, or a researcher's data-collection script — CE treats them identically. There is no special-cased code path inside CE for any particular receiver. This is what "CE stays clean" means in concrete terms: any automated platform built on top of CE uses the same public webhook capability that any self-hoster has.

**Minimal payloads.** Event types today are `test.ping`, `event.created`, `event.deleted`, `event.allocated`, `event.over_cap` and `workspace.delete_requested`. Payloads carry ids, timestamps and at most a rounded headcount; no participant data. Each is queued in the same transaction as the change it reports.

**Signed at the wire.** Every outbound POST carries a `Moimio-Signature: ts=<unix>;h1=<hex>` header, where `h1` is an HMAC-SHA256 over `"<ts>:" + raw body`, re-signed on every attempt. Receivers verify with a per-endpoint secret that was shown once at endpoint creation. The signing scheme is symmetric with Paddle's inbound convention so receivers can reuse code if they're already handling Paddle webhooks.

**At-least-once delivery.** Failed deliveries (non-2xx, 15 s timeout, connection error; redirects are not followed) retry on a 30s / 2min / 10min / 1h / 6h schedule (about 7¼ hours, six attempts in all). Receivers are expected to be idempotent on the envelope's `event_id` field. After 5 consecutive failed attempts the endpoint is marked `degraded`; after 20 it is `disabled` and requires manual re-enabling. There is one delivery row per event per endpoint, updated on each attempt, retained for `WEBHOOK_DELIVERY_RETENTION_DAYS` (default 30) for debugging.

**No reaching inward.** Since v1.0.4a, user-created endpoint URLs must be http(s) and resolve only to public addresses: private, loopback, link-local, CGNAT and similar targets are refused on create/edit and re-checked before every delivery (DNS rebinding). `WEBHOOK_ALLOW_PRIVATE_TARGETS=true` lifts this for self-hosters with an internal receiver. A small resolve-then-connect race remains and is on the backlog.

The admin UI is a Super-Admin-only section at `/admin/webhooks`. It is hidden when `FEATURE_OUTBOUND_WEBHOOKS=false`, when the user isn't a super admin, and on hosted workspaces (`FEATURE_ACCOUNT_PORTAL=true`), where the API is also read-only: every write, rotate, re-enable and test-fire returns 403 and only listing works (v1.0.4c). Delivery itself keeps running there, because the platform's own auto-registered endpoint (`managed_by=saas`, from `MOIMIO_WEBHOOK_URL`/`MOIMIO_WEBHOOK_SECRET`, hidden from the UI and exempt from the address check) depends on it.

Signing secrets are stored in plaintext in the `outbound_webhook_endpoints` table. CE is the *sender* of webhooks and must produce a fresh HMAC on every delivery — hash-only storage would make signing impossible after a restart. The "shown once via UI" UX is enforced at the API layer (GET responses never include the secret), which prevents accidental disclosure to humans but does not protect against full-DB leaks. Standard hosting trust and backup encryption are the protection at rest; an encrypted-column hardening with a master-key env var is candidate future work.

Background work — a worker tick every 30 seconds that sends every due pending delivery (first attempts and retries alike), and a delivery-log prune at 03:00 UTC — runs in an `AsyncIOScheduler` (APScheduler) instance attached to the FastAPI lifespan. No external worker service is required; jobs share the same async SQLAlchemy session machinery as request handlers.

Full integration guide for receivers: [`docs/webhooks.md`](docs/webhooks.md). Schema for the two backing tables: [`docs/data-model.md`](docs/data-model.md).

---

## 11. Where to read more

| Topic | Where to look |
|---|---|
| Schema specifics | [`docs/data-model.md`](docs/data-model.md) |
| Allocation algorithm | `backend/app/services/engine_service.py` (top-of-file docstring) |
| GDPR architecture | [`docs/gdpr-compliance.md`](docs/gdpr-compliance.md) |
| User-facing feature reference | [`docs/manual/README.md`](docs/manual/README.md) |
| Webhook integration recipe | [`docs/webhooks.md`](docs/webhooks.md) |
| API surface | `http://localhost:6121/docs` (auto-generated OpenAPI) |
| Translation system | [`TRANSLATION_RULE.md`](TRANSLATION_RULE.md) |
| Contribution mechanics | [`CONTRIBUTING.md`](CONTRIBUTING.md) |

---

*This document captures the principles as of v1.0.6. Significant architectural shifts will be reflected here; minor refinements live in the codebase and the public CHANGELOG.*
