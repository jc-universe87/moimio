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

Personal data stays inside the deployment. There is no Moimio cloud server in the CE edition; there is no analytics; there are no calls to external APIs during registration or allocation. Self-hosting means the organiser is the data controller and Moimio is not a sub-processor.

GDPR primitives are first-class:

- **Article 20 export** — a single click exports every record Moimio holds about a participant in a structured JSON file.
- **Article 17 erasure** — soft delete is one click; hard erasure is supported as a manual database operation (a first-class UI is post-1.0 backlog).
- **Per-event audit log** — `allocation_events` is append-only and records every state-changing operation on the allocation pipeline.
- **Structure-only backup mode** — backs up the event's *configuration* (categories, units, marks, custom fields, form layout) without participant data, for sharing event templates publicly without leaking PII.

Full detail in [docs/gdpr-compliance.md](docs/gdpr-compliance.md).

### 2.3 Volunteer-organiser-friendly, not enterprise-flexible

Moimio is built for **small and mid-sized event organisers** — churches, missions, retreats — running events of up to ~300 participants. Decisions are filtered through that lens.

A feature request that makes Moimio more enterprise-flexible at the cost of being harder to set up for a volunteer organiser is, almost always, the wrong direction. We accept lower flexibility ceilings to preserve the floor.

### 2.4 Doing obvious things well

Moimio prefers a smaller feature that's reliable over a larger feature that's clever. The allocation engine is intentionally a deterministic five-pass algorithm rather than a constraint solver or an optimisation problem — it produces the same output for the same input every time, and an organiser can read what it did and why.

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

### 4.1 Deterministic five-pass algorithm

Same inputs → same output, every time. The five passes, in order:

1. **Group-code clusters.** Families and friend groups (linked by a shared `group_code`) get placed together as a unit.
2. **Mark "together" clusters.** Participants sharing a mark configured to keep-together (e.g. all leaders in one room) get placed as a unit.
3. **Mark "split-evenly" pre-distribution.** Participants sharing a mark configured to spread evenly (e.g. one leader per room) get distributed across units before the open round-robin.
4. **Drain gender-restricted units, then round-robin the rest.** Gender-locked units fill first to capacity; remaining participants distribute round-robin into open units.
5. **Classify anyone unplaced** with a clear reason — e.g. "no compatible unit (gender restriction)", "all units at capacity".

Pass 1 takes precedence over pass 2 by design — group codes are an explicit family/friend signal; marks are a staff signal. If the two conflict, group codes win.

The full algorithm is documented in the top-of-file docstring of `backend/app/services/engine_service.py`.

### 4.2 Imbalance is by design

The engine produces a valid allocation, not the *most balanced* allocation. Capacities are respected; clusters are kept; gender restrictions are enforced. Within those constraints, the engine fills units in the order they appear, which can leave the last unit lighter than the others.

This is intentional. A "perfectly balanced" output would require either ignoring clusters (defeating the point) or shuffling cluster placements after the fact (producing non-determinism between runs). Organisers who want a tighter balance use **Reallocate everyone from scratch** with adjusted unit capacities — small capacity changes shift the rebalancing in predictable ways.

### 4.3 Two modes: top-up vs replace

- **Top-up** (`Allocate new participants only`) — keep existing assignments, place new participants only. Used after registration re-opens or after a manual fix the organiser wants to preserve.
- **Replace** (`Reallocate everyone from scratch`) — wipe the existing allocation, propose a fresh one. Default after engine setting changes.

Manual placements (drag-and-drop in the AllocationBoard) lock against subsequent **top-up** runs but not **replace** runs.

### 4.4 Append-only allocation events

Every state-changing operation on the allocation pipeline writes a row to `allocation_events`. The table is append-only at the application layer (no `UPDATE`, no `DELETE`). It serves three purposes:

- **Audit.** Who ran the engine, with what settings, at what time.
- **Reasoning surface.** When the engine places a participant, the reason — pass number, cluster ID, gender restriction match — is captured and surfaced in the InsightPanel.
- **Forensic recovery.** If something goes wrong, the history is reconstructable.

---

## 5. Generic allocation primitives

The original Phase 1 schema had three tables: `Room`, `Group`, `Team`. Phase 2 abandoned that for a single generic system.

- **`AllocationCategory`** — a named kind of allocation (e.g. "Rooms", "Small Groups", "Workshops"). Has a `rule_type`:
  - `exclusive` — one participant in only one unit (rooms, primary small groups).
  - `overlapping` — one participant in many units (sessions, workshops, shifts).
- **`AllocationUnit`** — a named slot within a category, with capacity and optional gender restriction.
- **`Allocation`** — links a participant to a unit. UNIQUE on `(participant_id, unit_id)`.

This generalisation is what lets organisers add their own categories ("Workshops", "Buses", "Meal shifts") without a schema change. New events come pre-seeded with **Rooms** and **Small Groups** as defaults, but the system has no special-casing for those names.

---

## 6. Marks and group codes

Two participant-tagging primitives serve different purposes; understanding the distinction is key to using either well.

### 6.1 Marks — staff-internal colour-coded tags

Marks are coloured badges attached by staff: "leader", "first-timer", "needs ground floor", "vegetarian". They are **staff-internal** — participants never see them — and **per-event** — a mark on Event A doesn't carry to Event B.

Each mark has an allocation behaviour configured per category:

- `together` — cluster marked participants in the same unit.
- `split_evenly` — distribute marked participants across units.
- `none` — purely visual, no engine effect.

A leader mark might be `together` for Rooms (leaders share a room) but `split_evenly` for Small Groups (one leader per group).

### 6.2 Group codes — registration-time family/friend identifiers

A `group_code` is a string assigned at registration time (e.g. `SMITH-742`). Participants entering the same code form a cluster that the engine keeps together at allocation time.

If a registrant doesn't enter one, Moimio auto-generates `STEM-NNN` (a stem derived from the surname plus a unique three-digit suffix, scoped to the event), and includes it in the confirmation email so the registrant can share it.

Group codes optionally scope to specific allocation categories — a family wants to share a room but not necessarily the same workshop. The `group_code_categories` JSONB field captures this.

The engine treats group-code clusters in pass 1, before any mark logic. This means group codes effectively override mark behaviours — if a married couple are both leaders and the leader mark is `split_evenly`, the engine will still keep them in the same room.

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

**Build-time parity.** A Python script (`frontend/scripts/validate-i18n-keys.py`) gates `npm run build` and refuses any build where a `t('key')` callsite has no matching key in the English source-of-truth dictionary. Keys must be in underscore form (`event.archive.confirm_title`); dot-form keys are a recurring bug pattern explicitly caught by the validator.

**No auto-translation.** New keys must be human-translated into all six locales in the same PR. English is the source of truth; missing keys in other locales fall back to English at runtime, but parity is the contract. Auto-translation services produce locale-specific drift that's hard to detect and worse to debug.

**The brand mark stays English.** The tagline **Gather · Organise** is not translated. It is the brand mark, not a product label.

Full detail in [TRANSLATION_RULE.md](TRANSLATION_RULE.md).

---

## 10. Outbound webhooks for integrations

From v1.0.0g, Moimio CE can POST signed HTTP notifications to URLs you configure, the moment a system event happens. This is the integration seam — wire Slack notifications, Zapier flows, custom scripts, accounting systems, anything that accepts inbound webhooks.

The subsystem is a deliberate architectural commitment, not a feature add. It has three load-bearing properties:

**Generic, not deployment-specific.** Moimio CE doesn't know who's listening on the other end of a webhook. The receiver might be a self-hoster's Zapier flow, an external billing layer, or a researcher's data-collection script — CE treats them identically. There is no special-cased code path inside CE for any particular receiver. This is what "CE stays clean" means in concrete terms: any automated platform built on top of CE uses the same public webhook capability that any self-hoster has.

**Signed at the wire.** Every outbound POST carries a `Moimio-Signature` header containing an HMAC-SHA256 over the raw body. Receivers verify with a per-endpoint secret that was shown once at endpoint creation. The signing scheme is symmetric with Paddle's inbound convention so receivers can reuse code if they're already handling Paddle webhooks.

**At-least-once delivery.** Failed deliveries retry on a 30s / 2min / 10min / 1h / 6h schedule (~7.5 hours total). Receivers are expected to be idempotent on the `event_id` field. After 5 consecutive failures the endpoint is marked `degraded`; after 20 it is `disabled` and requires manual re-enabling. Delivery rows are retained for 30 days (configurable) for debugging.

The admin UI is a Super-Admin-only section at `/admin/webhooks`. It is hidden when `FEATURE_OUTBOUND_WEBHOOKS=false` and when the user isn't a super admin. The capability gate exists so an operator who doesn't want integration surfaces can hide them entirely.

Signing secrets are stored in plaintext in the `outbound_webhook_endpoints` table. CE is the *sender* of webhooks and must produce a fresh HMAC on every delivery — hash-only storage would make signing impossible after a restart. The "shown once via UI" UX is enforced at the API layer (GET responses never include the secret), which prevents accidental disclosure to humans but does not protect against full-DB leaks. Standard hosting trust and backup encryption are the protection at rest; an encrypted-column hardening with a master-key env var is candidate future work.

Background work — retrying failed deliveries every 30 seconds, pruning the delivery log nightly — runs in an `AsyncIOScheduler` (APScheduler) instance attached to the FastAPI lifespan. No external worker service is required; jobs share the same async SQLAlchemy session machinery as request handlers.

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

*This document captures the principles as of v1.0.0. Significant architectural shifts will be reflected here; minor refinements live in the codebase and the public CHANGELOG.*
