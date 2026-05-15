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
  and optional gender restriction.
- **`Allocation`** — links a `Participant` to an `AllocationUnit`.
  UNIQUE across (participant_id, unit_id).

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
 │    └── AllocationUnit
 ├── Participant
 │    ├── group_code            (STEM-NNN, links related registrations)
 │    ├── group_code_categories (JSONB: null = all categories, [uuid,...] = scoped)
 │    ├── registration_status   (pending/confirmed/cancelled)
 │    ├── participant_number    (sequential per event; shown in table + email)
 │    ├── override_group_room   (opt-out of group-aware allocation)
 │    ├── CustomFieldValue      (EAV response data)
 │    ├── CheckInValue          (per-field tick state)
 │    ├── MarkAssignment        (badges assigned to this participant)
 │    ├── Allocation            (participant ↔ AllocationUnit links)
 │    └── ParticipantPreferenceRequest (opt-in group preference submissions)
 └── Note                       (polymorphic; attachable to any of the above)

User
 ├── role                       (super_admin | staff)
 ├── can_manage_users, can_create_events (fine-grained global capabilities)
 ├── password_reset_token + password_reset_expires
 └── UserPreferences            (language, date format, timezone)
```

## The 19 Tables

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
| `allocation_units` | Named slots within a category. Capacity + gender restriction optional. |
| `allocations` | Participant↔Unit links. UNIQUE(participant_id, unit_id). |
| `participant_preference_requests` | "I'd like to be with so-and-so" submissions from the registration form (off by default per event). |
| `mark_definitions` | Colour-badge types per event ("Leader", "New to us", "Allergic to X"). |
| `mark_assignments` | Badge↔participant links. |
| `checkin_fields` | Custom tick columns for check-in mode ("Arrived", "Picked up pack", "Paid cash"). |
| `checkin_values` | Per-field tick state for each participant. |
| `notes` | Polymorphic. Attaches to any of: participant, event, allocation_category, allocation_unit, allocation, mark_assignment. |
| `outbound_webhook_endpoints` | (v1.0.0g) Registered HTTP receivers for outbound webhook notifications. Name, URL, signing secret (plaintext at-rest — see [ARCHITECTURE.md § 10](../ARCHITECTURE.md#10-outbound-webhooks-for-integrations)), subscribed event types, health state. `managed_by` distinguishes admin-created (`user`) from auto-registered (`saas`) endpoints — the latter are hidden from the admin UI. |
| `outbound_webhook_deliveries` | (v1.0.0g) Append-only log of every delivery attempt. One row per attempt (so a retried event produces multiple rows sharing the same `event_id`). Pruned daily by a scheduled job; retention configurable via `WEBHOOK_DELIVERY_RETENTION_DAYS` (default 30 days). |

## Conventions

- **Primary keys:** UUID v4, generated server-side.
- **Timestamps:** `created_at` on all tables. `updated_at` on mutable entities (auto-maintained server-side).
- **Foreign keys:** `ON DELETE CASCADE` almost everywhere — deleting an event removes everything under it.
- **Soft delete:** Used on `participants` only, via a `deleted_at` timestamp. Everything else is hard delete (cascading from the parent). `is_archived` on `events` is a third pattern — neither soft delete nor cascade — used to move events out of the active workspace without losing the data.
- **Enums:** stored as PostgreSQL native enums (lowercase labels).

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

Transitions are driven by delivery outcomes: `active` → `degraded` after 5 consecutive failed deliveries; `degraded` → `disabled` after 20. Recovers to `active` on first successful delivery (from `degraded`) or manual re-enable (from `disabled`). A separate `is_active` boolean handles admin-paused endpoints — orthogonal to this state machine.

### `WebhookEndpointManagedBy` (table: `outbound_webhook_endpoints`)
```
user | saas
```

`user` = created by an admin through the Webhooks admin UI; fully editable. `saas` = auto-registered at boot via env vars; hidden from UI and not user-editable. Pattern borrowed from managed Kubernetes — platform-created infrastructure objects that users can't break.

### `WebhookDeliveryStatus` (table: `outbound_webhook_deliveries`)
```
pending | success | failed | exhausted
```

`pending` = waiting for first attempt or scheduled retry. `success` = 2xx response received. `failed` = transient failure, retry scheduled. `exhausted` = all retries used up.

## Participant — Key Fields (post-v20)

`group_code` (formerly `family_tag`) is a human-readable code shared
by related registrations (e.g. a family registering together).
Format: `STEM-NNN`, scoped per event. Auto-generated server-side
when the registrant doesn't supply one (`SURNAME-` plus a random
three-digit suffix), and included in the registration confirmation
email.

`group_code_categories` (JSONB, nullable): exists in the schema as
a future-facing field for limiting a group code's effect to specific
categories. **Not currently enforced by the engine** — left as `NULL`
in practice; group codes apply to all exclusive-rule categories.

`override_group_room` (bool): if true, the allocation engine
ignores this participant's group code when placing them into
exclusive-rule categories. Still respected for overlapping
categories.

`participant_number` (int, per-event sequential): lightweight
human-friendly ID, shown in people tables and confirmation emails.
Assigned via `MAX(participant_number) + 1` per event. Race
condition possible under high concurrent registration but
acceptable for Moimio's target scale (≤150 participants).

## Allocation Engine — Settings

`AllocationCategory.settings` is a JSON column. Real default shape (per `engine_service.DEFAULT_ENGINE_SETTINGS`):

```json
{
  "engine": {
    "use_group_codes": true,
    "group_remaining_by_gender": true,
    "split_oversized_groups": true,
    "include_pending_in_allocation": true,
    "mark_priorities": [
      {"id": "uuid-of-mark-def", "behaviour": "together"},
      {"id": "uuid-of-other-mark", "behaviour": "split"}
    ]
  }
}
```

`mark_priorities` accepts both shapes for backward compatibility: the legacy form is a list of UUID strings (cluster behaviour comes from the global `MarkDefinition.cluster_behaviour`), and the new form is a list of `{id, behaviour}` objects (per-category override of the global behaviour). New writes use the object form.

`exclusive_group_codes` is a separate boolean **column on `allocation_categories`**, not nested under `settings.engine`. When true, group-code clusters claim their unit fully on Pass 1.

Editable by anyone with category write access. Used by `engine_service.run_engine()` when generating an allocation proposal.

## Notes — Polymorphism

Notes are attached via `notable_type` (string, indexed) +
`notable_id` (UUID). Supported `notable_type` values:
- `participant`, `event`, `allocation_category`,
  `allocation_unit`, `allocation`, `mark_assignment`

No cascading FK constraints on notes — cleanup is the application
layer's responsibility when parents are deleted. This is a
pragmatic trade-off: polymorphic FKs across multiple parent tables
would require trigger machinery that isn't worth the complexity at
Moimio's scale.

**Visibility:**
- `is_published = false` — visible only to the author.
- `is_published = true` — visible to the whole organising team.
  Who can publish is controlled by `Event.settings.published_notes_writers`.
- Participants never see notes.

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
  Each surface gets one of `""`/null (no access), `"read"`, or `"write"` — except `checkin`, which is an object: `access` follows the same convention; `pre_event` is a boolean sub-flag granting access before the event starts (relevant during the Registration phase). The `event_admin` role has implicit write on all surfaces and ignores the JSON.

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
```

On backend container start, `alembic upgrade head` runs
automatically. Idempotent — if already at head, no-ops and proceeds
to uvicorn. See `backend/Dockerfile` CMD line.

## What this document is not

- A column-by-column reference. See `backend/app/models/` for that.
- A Pydantic schema reference. See `backend/app/schemas/`.
- An API reference. See the auto-generated OpenAPI docs at
  `http://localhost:6121/docs`.
