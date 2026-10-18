# Moimio CE — Data Model

> This document describes the *shape* and *intent* of the schema —
> why things are where they are, not every column. For the
> per-table column list and Pydantic schemas, read the source:
> `backend/app/models/` and `backend/app/schemas/`. The auto-generated
> OpenAPI reference at `http://localhost:6121/docs` is the API surface
> source of truth.

## Design Principle

Central entity: **Participant**. Everything relational flows from
Participant → Event, and optionally from Participant → Allocation.

The Phase 1 plan called for three separate allocation tables (`Room`,
`Group`, `Team`). Phase 2 replaced that with a single generic system:

- **`AllocationCategory`** — a named kind of allocation (e.g.
  "Rooms", "Small Groups", "Workshops"). Has a `rule_type`:
  - `exclusive` — one participant can be in only one unit of this
    category. Used for sleeping rooms and primary small groups.
  - `overlapping` — a participant can be in several units of this
    category simultaneously. Used for sessions, workshops, shifts.
- **`AllocationUnit`** — a named slot within a category (e.g.
  "Room 3", "Red team", "Pottery workshop"). Has a capacity
  (`0` = no capacity limit, since v1.0.3), an optional gender
  restriction, an optional mark restriction, and an `is_kept`
  ("keep as-is") flag.
- **`Allocation`** — links a `Participant` to an `AllocationUnit`.
  UNIQUE across (participant_id, unit_id).
- **`AllocationCategoryExclusion`** — keeps one participant out of one
  category (v1.0.5). UNIQUE(allocation_category_id, participant_id).

This replaces every per-type table from the Phase 1 plan.

## Entity Overview

```
Event
 ├── EventFieldConfig           (per-event toggles for registration form fields)
 ├── EventUserAssignment        (user ↔ event, with role + inline permissions JSON)
 ├── CustomFieldDefinition      (EAV schema for event-specific form fields)
 ├── CheckInField               (custom tick columns for check-in mode)
 ├── MarkDefinition             (colour badges for staff-visible participant tagging)
 ├── AllocationCategory
 │    ├── AllocationUnit
 │    └── AllocationCategoryExclusion (participant kept out of this category)
 ├── AllocationEvent            (append-only allocation history)
 ├── Participant
 │    ├── group_code            (STEM-NNN, links related registrations)
 │    ├── group_code_categories (JSONB: retired v1.0.5, unread)
 │    ├── registration_status   (pending/confirmed/cancelled)
 │    ├── participant_number    (sequential per event; shown in table + email)
 │    ├── override_group_room   (stored, read by nothing; see below)
 │    ├── CustomFieldValue      (EAV response data)
 │    ├── CheckInValue          (per-field tick state)
 │    ├── MarkAssignment        (badges assigned to this participant)
 │    ├── Allocation            (participant ↔ AllocationUnit links)
 │    └── ParticipantPreferenceRequest (opt-in group preference submissions)
 └── Note                       (polymorphic; event, participant, category or unit)

User
 ├── role                       (super_admin | staff)
 ├── can_manage_users, can_create_events (fine-grained global capabilities)
 ├── password_reset_token + password_reset_expires
 └── UserPreferences            (language, date format, timezone)

Instance-wide (no event or user parent)
 ├── WorkspaceSettings          (single row: privacy_notice_url)
 └── OutboundWebhookEndpoint
      └── OutboundWebhookDelivery
```

## The 22 Tables

| Table | Purpose |
|-------|---------|
| `users` | Organising team accounts (separate from participants). Roles + global capability flags. |
| `user_preferences` | Per-user UI settings (language, date format, timezone). |
| `events` | Top-level event records. Status workflow: draft→open→closed; archival is an orthogonal `is_archived` boolean flag (see below). |
| `event_field_configs` | Which registration fields are enabled/required per event. |
| `event_user_assignments` | User↔event links with role + inline permissions JSON. Replaces an earlier `StaffGroup` table — permissions now live directly on the assignment. |
| `participants` | The central entity. One row per person registered to an event. |
| `custom_field_definitions` | EAV schema rows ("T-shirt size", "Dietary needs"). |
| `custom_field_values` | EAV response rows (text storage, app-layer typed). |
| `allocation_categories` | Named kinds of allocation per event. `rule_type` = exclusive/overlapping. `settings` JSON holds engine config. |
| `allocation_units` | Named slots within a category. `capacity` is NOT NULL; `0` means no capacity limit (v1.0.3). Optional `gender_restriction`, optional `mark_restriction` (FK to `mark_definitions`, SET NULL), and `is_kept`, which freezes the unit's occupants on re-allocation. |
| `allocations` | Participant↔Unit links. UNIQUE(participant_id, unit_id). |
| `allocation_category_exclusions` | (v1.0.5) Participants kept out of one category. UNIQUE(allocation_category_id, participant_id); both FKs cascade; `created_by` is SET NULL when the user is deleted. The engine drops excluded people before any pass; committing a placement for one lifts the exclusion. |
| `allocation_events` | Append-only allocation history: `event_type` is `assign`, `unassign`, `exclude` or `include`, plus a `source` (manual, engine commit, cancellation, exclusion, ...). Snapshots unit and category names; `participant_id`, `unit_id`, `category_id` and `actor_user_id` are SET NULL on delete, so history survives erasure without naming the person. `action_id` groups the rows one action wrote; `meta` carries engine placement reasons. Cascades with the event. |
| `participant_preference_requests` | "I'd like to be with so-and-so" submissions from the registration form (off by default per event). The organising team reads these and acts by hand; nothing in the engine acts on them. Their `category_scope` column, a limit to particular group types, was never enforced and never had a screen: it was retired in v1.0.5 and is unread; the column is still present in v1.0.6 and its removal is planned for a later migration. |
| `mark_definitions` | Colour-badge types per event ("Leader", "New to us", "Allergic to X"). |
| `mark_assignments` | Badge↔participant links. |
| `checkin_fields` | Custom tick columns for check-in mode ("Arrived", "Picked up pack", "Paid cash"). |
| `checkin_values` | Per-field tick state for each participant. |
| `notes` | Polymorphic. Attaches to a participant, event, category or unit (see below). `author_id` is nullable, SET NULL on user delete. |
| `workspace_settings` | (v1.0.6) Single row (`id = 1`, integer key) of installation-wide settings an admin edits on screen. Only column so far: `privacy_notice_url`, shown on the public registration form after the consent sentence; null shows nothing. |
| `outbound_webhook_endpoints` | (v1.0.0g) Registered HTTP receivers for outbound webhook notifications. Name, URL, signing secret (plaintext at-rest — see [ARCHITECTURE.md § 10](../ARCHITECTURE.md#10-outbound-webhooks-for-integrations)), subscribed event types, health state. `managed_by` distinguishes admin-created (`user`) from auto-registered (`saas`) endpoints — the latter are hidden from the admin UI. |
| `outbound_webhook_deliveries` | (v1.0.0g) Delivery log. One row per event per subscribed endpoint, **updated in place** on each attempt: `attempt`, `status`, `next_attempt_at`, `response_status`, `duration_ms` and `error` reflect the latest attempt. Rows share an `event_id` only when several endpoints received the same event. (The model's docstring still says "one row per attempt"; the service does not do that.) Pruned daily at 03:00 UTC by a scheduled job, by `created_at`; retention configurable via `WEBHOOK_DELIVERY_RETENTION_DAYS` (default 30 days). Cascades when the endpoint is deleted. |

## Conventions

- **Primary keys:** UUID v4, generated server-side. Exception: `workspace_settings` uses an integer key fixed at 1.
- **Timestamps:** `created_at` on almost all tables (`allocation_events` uses `occurred_at`; `workspace_settings` has only `updated_at`). `updated_at` on mutable entities (auto-maintained server-side).
- **Foreign keys:** `ON DELETE CASCADE` on most event-scoped children, but not all: `participants.event_id`, `event_field_configs.event_id`, `custom_field_definitions.event_id`, `custom_field_values.participant_id`/`field_id` and `participant_preference_requests.event_id`/`participant_id` have no ON DELETE rule, and notes have no FK at all. Deleting an event therefore goes through `event_service.delete_event`, which deletes children explicitly in order. References to users are SET NULL (history, authorship) or CASCADE (preferences, assignments), so any user can be deleted (v1.0.5); their unpublished notes are deleted first.
- **Soft delete:** Used on `participants` only, via a `deleted_at` timestamp. Everything else is hard delete. `is_archived` on `events` is a third pattern — neither soft delete nor cascade — used to move events out of the active workspace without losing the data.
- **Enums:** `event_status`, `registration_status`, `user_role` and the three webhook enums are PostgreSQL native enums (lowercase labels). Several other enumerations are plain strings validated in Python: `allocation_categories.rule_type`, `mark_definitions.cluster_behaviour`, `event_user_assignments.role`, and `allocation_events.event_type`/`source`.

## Core Enums

### `EventStatus` (table: `events`)
```
draft | open | closed | archived
```

### `RegistrationStatus` (table: `participants`)
```
pending | confirmed | cancelled
```

### `UserRole` (table: `users`)
```
super_admin | staff
```

`event_admin` is *not* a global role. It only exists at the per-event assignment level (`event_user_assignments.role`).

### `WebhookEndpointState` (table: `outbound_webhook_endpoints`)
```
active | degraded | disabled
```

Transitions are driven by delivery outcomes, counted per attempt in `consecutive_failures`: `active` → `degraded` after 5 consecutive failed attempts; → `disabled` after 20. Recovers to `active` on the first successful delivery (from `degraded`) or on manual re-enable (from either state, which also resets the counter). A separate `is_active` boolean handles admin-paused endpoints — orthogonal to this state machine. Pending deliveries for a paused or disabled endpoint are marked `exhausted` when they come due.

### `WebhookEndpointManagedBy` (table: `outbound_webhook_endpoints`)
```
user | saas
```

`user` = created by an admin through the Webhooks admin UI; fully editable (except on hosted workspaces, where the API is read-only). `saas` = registered or updated at every boot from `MOIMIO_WEBHOOK_URL`/`MOIMIO_WEBHOOK_SECRET`; hidden from the UI and API, not user-editable, and exempt from the private-address check. Pattern borrowed from managed Kubernetes — platform-created infrastructure objects that users can't break.

### `WebhookDeliveryStatus` (table: `outbound_webhook_deliveries`)
```
pending | success | failed | exhausted
```

`pending` = waiting for first attempt or scheduled retry (a failed attempt with retries left goes back to `pending`). `success` = 2xx response received. `exhausted` = all retries used up, or the endpoint was deleted, paused or disabled before the attempt. `failed` exists in the enum but the current service never writes it.

## Participant — Key Fields (post-v20)

`group_code` (formerly `family_tag`) is a human-readable code shared
by related registrations (e.g. a family registering together).
Format: `STEM-NNN`, scoped per event. Auto-generated server-side
when the registrant doesn't supply one (`SURNAME-` plus a random
three-digit suffix), and included in the registration confirmation
email.

`group_code_categories` (JSONB, nullable): **RETIRED in v1.0.5, and
unread from that release on.** It limited one person's group code to
particular group types, and until v1.0.5 the engine's PASS 1 did
enforce it — this page previously said it did not, which was wrong from
the first public commit. No screen in any of the six languages could
see or set it, no CSV column carried it, and no release announced it;
the only way in was a hand-made API call. A group code now applies in
every group type where `use_group_codes` is on. The column stays so a
rollback still finds what it expects; it is still present in v1.0.6, and
backups and the per-person GDPR export keep carrying it until it is
dropped in a later migration. Note the stored value is the JSON `null`
literal, not SQL NULL.

`override_group_room` (bool): stored, accepted by the participant
update API, carried in backups and the GDPR export, but **read by
nothing**: the allocation engine does not consult it. Earlier
versions of this page said it opted a person out of group-code
clustering; that was never implemented. Its removal is planned.

`participant_number` (int, per-event sequential): lightweight
human-friendly ID, shown in people tables and confirmation emails.
Assigned via `MAX(participant_number) + 1` per event. Race
condition possible under high concurrent registration but
acceptable for Moimio's target scale (≤150 participants).

## Allocation Engine — Settings

`AllocationCategory.settings` is a JSON column. A new category stores only the first three keys below; the engine fills any missing key from `engine_service.DEFAULT_ENGINE_SETTINGS`, so the effective defaults are:

```json
{
  "engine": {
    "use_group_codes": true,
    "group_remaining_by_gender": true,
    "split_oversized_groups": true,
    "include_pending_in_allocation": true,
    "equalise_after_allocation": true,
    "mark_priorities": [
      {"id": "uuid-of-mark-def", "behaviour": "together"},
      {"id": "uuid-of-other-mark", "behaviour": "split"}
    ]
  }
}
```

(The default for `mark_priorities` is `[]`; the entries above are an example.) `equalise_after_allocation` (v1.0.0e) runs the final sweep that moves whole movable clusters between units to even out occupancy. `mark_priorities` accepts both shapes for backward compatibility: the legacy form is a list of UUID strings (cluster behaviour comes from the global `MarkDefinition.cluster_behaviour`), and the new form is a list of `{id, behaviour}` objects (per-category override of the global behaviour). Behaviour values are `together`, `split` and `none`. Only marks listed here affect the engine, in list order (v1.0.4e). New writes use the object form.

`exclusive_group_codes` is a separate boolean **column on `allocation_categories`**, not nested under `settings.engine`. When true, group-code clusters claim their unit fully on Pass 1.

Editable by event admins (and super admins) through `PATCH /api/events/{event_id}/allocation-categories/{category_id}`. Used by `engine_service.run_engine()` when generating an allocation proposal.

## Notes — Polymorphism

Notes are attached via `notable_type` (string, indexed) +
`notable_id` (UUID). Values the frontend writes, and that event
deletion and backup/restore handle:
- `participant`, `event`, `category`, `unit`

The API accepts any string; `event_service.delete_event` also sweeps the
legacy unit types `room` and `group`.

No FK constraints on `notable_id` — cleanup is the application
layer's responsibility when parents are deleted. Event deletion does
it; deleting a single unit, category or participant row does not. This is a
pragmatic trade-off: polymorphic FKs across multiple parent tables
would require trigger machinery that isn't worth the complexity at
Moimio's scale.

**Visibility:**
- `is_published = false` — visible only to the author.
- `is_published = true` — visible to the whole organising team.
  `Event.settings` carries a default `published_notes_writers` key,
  but the notes API does not currently enforce it: any authenticated
  user can create a published note.
- Participants never see notes, except that published participant
  notes are included in that participant's GDPR data export.

**Authorship:** `author_id` is SET NULL when the user is deleted, and
that user's unpublished notes are deleted first, so a null author always
means a published note by a removed user.

## Permissions Model — Key Shape

Global (on `users`):
- `role`: `super_admin` or `staff` (only these two; `event_admin` is per-event, not global).
- `can_manage_users`, `can_create_events`: fine-grained capabilities.
- Super admin bypasses all per-event permission checks.

Per-event (on `event_user_assignments`):
- `role`: `event_admin` or `staff`.
- `permissions`: inline JSON. Real shape (v0.81+):
  ```json
  {
    "people":   "write",
    "organise": "read",
    "checkin":  {"access": "write", "pre_event": false},
    "reports":  "read",
    "marks":    "write"
  }
  ```
  `people` and `organise` take `""`/null (no access), `"read"`, or `"write"`; `reports` is only ever `"read"` or null; `marks` is only ever `"write"` or null (reading marks comes with event access); `checkin` is an object: `access` follows the same convention; `pre_event` is a boolean sub-flag granting access before the event starts (relevant during the Registration phase). The `event_admin` role has implicit write on all surfaces and ignores the JSON.

**Migration note:** legacy assignments may store `checkin` as a flat string (`"write"` or `"read"`). The `/api/my-events` endpoint normalises both shapes to the α-shape on read; the migration `75a00000_checkin_permission_alpha_shape.py` converts on-disk rows.

## Migrations

All schema changes are managed by Alembic. Current migrations live
in `backend/alembic/versions/`:

```
50b00000_baseline.py
50c3a00000_add_category_confirmed.py
50e1d00000_staff_groups_removed.py
50f00000_marks_audit_trail.py
50f20000_mark_assignment_audit.py
50i00000_events_is_archived.py
50j00000_remove_event_admin_role.py
50q00000_enum_labels_lowercase.py
60a00000_allocation_events.py
74a00000_v074_engine_spec.py
75a00000_checkin_permission_alpha_shape.py
85a00000_custom_field_show_in_form.py
100g00000_outbound_webhooks.py
100y00000_add_over_cap_signalled.py
101e00000_add_mark_restriction_and_is_kept.py
103a00000_capacity_zero_means_no_limit.py
104a00000_localised_default_group_type_names.py
104i00000_allocation_category_exclusions.py
104j00000_allocation_event_action_id.py
104zb0000_notes_author_nullable.py
104zd0000_user_deletion_settled.py
106a00000_workspace_settings.py
```

Migration ids use internal development numbers, which do not always
match public release numbers (for example `104i00000` shipped in v1.0.5).

On backend container start, `alembic upgrade head` runs
automatically. Idempotent — if already at head, no-ops and proceeds
to uvicorn. See `backend/Dockerfile` CMD line.

## What this document is not

- A column-by-column reference. See `backend/app/models/` for that.
- A Pydantic schema reference. See `backend/app/schemas/`.
- An API reference. See the auto-generated OpenAPI docs at
  `http://localhost:6121/docs`.
