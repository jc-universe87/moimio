# Glossary

Terms used throughout the Moimio documentation, in the order you'll most likely encounter them. For broader concepts (the product itself, the allocation engine workflow, etc.), see the [User Manual](manual/README.md).

---

## Core concepts

### Event

The top-level container for everything else. An event represents a single gathering — a retreat weekend, a conference, a youth camp. Participants register *to an event*; allocations are *within an event*; staff are assigned *to an event*. Events have a status that moves through `draft` → `open` → `closed`, and a separate boolean `is_archived` flag that can be set independently to file the event away (see [Archive](#archive)).

### Participant

A person registered to an event. This is the central entity in Moimio — almost every other record (allocation, mark, custom field value, note) hangs off a participant.

Note that a *participant* is different from a *user*. Users are organising-team accounts (admins and staff with login access). Participants are the people attending the event. They are deliberately separate entities — most participants will never log in to anything.

### Registration

The act of a participant signing up for an event, typically through the public registration form. A registration produces a participant record with a `registration_status` of `pending`, `confirmed`, or `cancelled`.

### Confirmation

The transition from `pending` to `confirmed` registration status. Triggered either by the participant clicking a link in their confirmation email, or by an admin confirming on their behalf. Confirmed participants are the pool the allocation engine works from.

---

## Allocation

### Allocation Category

A named kind of allocation defined per event. Two categories — **Rooms** and **Small Groups** — are created by default for every new event; you can rename, delete, or add to them. Categories have a **rule type**:

- **Exclusive** — a participant belongs to *one* unit in this category at a time. Rooms are the canonical example.
- **Overlapping** — a participant can belong to *several* units in this category simultaneously. Workshops, sessions, or shifts.

### Allocation Unit

A specific slot within a category. If "Rooms" is the category, then "Room 3" or "The Lakeview Suite" are units. Units have a capacity and an optional gender restriction.

### Allocation

The link between a specific participant and a specific unit. The same participant can have multiple allocations (one per category for exclusive categories, several per category for overlapping ones).

### Capacity

The maximum number of participants a unit can hold. From v1.0 onwards capacity is required on every unit — there's no concept of an "uncapped" unit.

### Gender restriction

A property on a unit that limits placement to participants of a specified gender. Three values: `none` (default — anyone can be placed here), `male`, `female`. Participants whose gender is unknown cannot be placed in gender-restricted units.

---

## Allocation engine

### Allocation engine

The deterministic algorithm that proposes a complete allocation in one shot, given the current participants, units, and configured engine settings. Run, review, override, or re-run as needed. See [Manual section 6](manual/06-allocation-engine.md) for the full algorithm.

### Pass

The engine works in five sequential passes (PASS 1 through PASS 5). Each pass handles a different concern: cluster placement, mark-based grouping, gender-restricted draining, round-robin filling, classification of anything unplaced.

### Cluster

Two or more participants the engine should try to keep together — usually because they share a group code (a family or friend group), but sometimes because they share a mark configured to "keep together". A "cluster of one" (a single participant alone with their group code) is not treated as a cluster; they round-robin like any other individual.

### Round-robin

The engine's default placement strategy for individuals (PASS 4b). It walks units in capacity-ascending order, placing one participant per unit per cycle. Skips ineligible or full units. Produces a fair fill across the available space.

### Drain (PASS 4a)

The engine's strategy for gender-restricted units. The engine "drains" eligible-gender participants from the remaining pool into each restricted unit in turn (smallest capacity first), filling them as fully as possible before moving on to the unrestricted pool. This avoids the classic small-event problem of restricted rooms ending up half-empty because the algorithm got distracted.

### Unplaced

A participant the engine could not place. Each unplaced participant comes with a reason: `cluster_oversized_split_disabled`, `gender_unknown_no_mixed_unit_available`, or `no_capacity_remaining`. Admins resolve these manually.

---

## Group codes and clustering

### Group code

A short human-readable code shared between related registrations to keep them allocated together. Format: `STEM-NNN` (e.g. `SMITH-742`), scoped per event. A family registers with the same group code; the engine treats them as a cluster.

If a registrant doesn't enter a code, Moimio derives the stem from their last name and appends a unique three-digit suffix. If a registrant types only a stem (e.g. `SMITH` without a number), the same applies — a unique suffix is added before saving. This is collision-safe: two unrelated families both typing `SMITH` end up with different codes (`SMITH-742` and `SMITH-883`) and don't accidentally cluster together. A registrant who wants to join an existing cluster types the full code (`SMITH-742`); that's saved verbatim.

The final group code is included in the registration confirmation email so the registrant can share it with anyone else who'd like to be grouped with them.

(The codebase still has a few legacy references to `family_tag` — the previous name for this concept, kept around for backwards compatibility. They mean the same thing.)

### Override group room

A per-participant flag. When set, the participant's group code is ignored by the engine for **exclusive-rule categories** (rooms etc.). Useful for "I'm here with my family but I'd actually prefer a single room." Overlapping categories still respect the group code.

### Exclusive group codes

A per-category toggle. When on, a group-code cluster *fully claims* the unit it lands in — no other participants are placed there even if leftover capacity remains. Useful when you don't want to fill spare beds in a room with random individuals.

### Cluster behaviour (per-mark)

For marks that should influence allocation, three behaviours:

- **Keep together** — participants sharing this mark form a sub-cluster (PASS 2). Placed together where possible.
- **Spread evenly** — participants sharing this mark are distributed across units (PASS 3). One leader per room, that sort of thing.
- **No effect** — the mark is staff-visual only, ignored by the engine.

### Mark priority

When a participant has more than one mark, only the highest-priority mark drives engine behaviour. Priority and cluster behaviour are configured **per category in the engine-settings popover** (next to the Auto-Allocate button on the AllocationBoard) — *not* in the mark editor itself. This means the same mark can have different priorities and behaviours in different categories — e.g. "Leader" set to *Keep together* in Rooms but *Spread evenly* in Small Groups.

---

## Marks and tagging

### Mark

A colour-coded badge attached to a participant. Free-form — organisers create their own marks per event ("Leader", "First-timer", "Allergic to nuts", "Needs ground floor", "Has guitar"). Visible to staff in the admin UI; never visible to participants.

### Mark assignment

The link between a participant and a mark. A participant can have multiple mark assignments.

### Mark definition

The mark itself, including its name, colour, and engine behaviour. Defined per event, in the marks editor.

---

## Custom fields and check-in

### Custom field

An extra field added to the registration form, beyond Moimio's built-ins. Defined per event using a simple EAV schema. Field types: text, number, select (single choice), boolean (yes/no), date. "T-shirt size", "Dietary requirements", "Have you been before?" are typical examples.

### Check-in field

A custom tick column for the day participants arrive. "Arrived", "Picked up welcome pack", "Paid balance in cash", "Signed liability waiver" — anything you'd otherwise track on a clipboard.

---

## People and permissions

### User

An organising-team account with login access. Distinct from a *participant* (a person attending the event). Users have a global role and per-event assignments.

### Role

A user's global authorisation level. Two values: `super_admin` (system-wide access) and `staff` (event-scoped, must be assigned to specific events). The previous `event_admin` global role was retired in favour of a per-event role on the assignment record. Two capability flags (`can_manage_users`, `can_create_events`) sit alongside the role and add fine-grained system-level abilities.

### Per-event role

The role a Staff user has on a specific event, set on their `EventUserAssignment`. Two values: **Event Admin** (full access; per-surface permissions ignored) and **Staff** (per-surface permissions honoured). Independent of the user's global role — a Staff user can be Event Admin on event A and a permission-limited Staff member on event B.

### Permission surface

A scope of access within an event, granted on a per-staff-per-event basis. Five surfaces with different shapes:

- `people`: read / write / none (dropdown)
- `organise`: read / write / none (dropdown)
- `marks`: write / none (checkbox — read is implicit with event access)
- `checkin`: write / none (checkbox), plus a sub-toggle **Access before the event starts** (granted only when checkin write is on; lets the staff member configure check-in columns and access the panel during the Registration phase).
- `reports`: read / none (checkbox)

Event Admins implicitly have full access everywhere; per-surface permissions are ignored for them.

### Note

A free-text memo attached to any major entity (participant, allocation, mark assignment, event). Notes can be **private** (visible only to the author) or **published** (visible to the whole organising team). Participants never see notes regardless of state.

---

## Data lifecycle

### Soft delete

The default delete behaviour. Sets a `deleted_at` timestamp on the record; subsequent queries filter it out, but the record physically remains and can be restored. The GDPR data export deliberately includes soft-deleted records — a participant invoking right-of-access *after* asking to be removed is exactly the case where the export must still work.

### Manual erasure

Full physical removal of a record from the database. Moimio v1.0 does not ship a one-click hard-purge UI; for the rare case where regulatory context demands physical removal beyond soft delete, the operation is currently performed as a manual SQL deletion against the soft-deleted record. A first-class hard-purge UI is on the post-1.0 backlog.

### Archive

A reversible "filed away" state for events. Archived events become read-only for everyone, are excluded from the Active and Past tabs of the events list, and are shown in a separate Archived tab; their data stays intact and is still searchable, exportable, and restorable. Different from deletion — and reversible: a Super Admin can unarchive at any time, returning the event to whichever status it was in.

### Participant number

A small per-event integer assigned to each participant on registration. Used in confirmation emails, the participants table, sign-in sheets, and as the human-friendly identifier for preference requests. Not a primary key — Moimio uses UUIDs internally — just a lightweight number for humans.

---

## Documentation conventions

### "v1.0", "v0.x"

`v1.0` is the first public release. Earlier `v0.x` references in the source code, commit messages, and internal documentation correspond to development iterations leading up to v1.0; they are not separate published releases.

### "The engine"

Throughout the docs, "the engine" without qualification means the allocation engine. It's the only engine in Moimio.

### "The board" / "AllocationBoard"

The drag-and-drop UI for reviewing and adjusting an allocation, accessed under **Organise** in the admin nav.

### "InsightPanel"

A slide-in panel that shows everything Moimio holds about a single participant — registration data, marks, allocations, notes, audit history. In v1.0 the InsightPanel is reachable via the **(i)** icon next to a participant's name in the **AllocationBoard** (Organise page) or the **Check-in panel**. It is **not** opened from the People page (the People page focuses on table operations and inline editing).
