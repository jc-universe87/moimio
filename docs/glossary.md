# Glossary

Terms used throughout the Moimio documentation, in the order you'll most likely encounter them. For broader concepts (the product itself, the allocation engine workflow, etc.), see the [User Manual](manual/README.md).

---

## Core concepts

### Event

The top-level container for everything else. An event represents a single gathering — a retreat weekend, a conference, a youth camp. Participants register *to an event*; allocations are *within an event*; staff are assigned *to an event*. Events have a status that moves through `draft` → `open` → `closed`, and a separate boolean `is_archived` flag that can be set independently to file the event away (see [Archive](#archive)).

### Phase

The stage an event is in, shown across the top of the event. There are three:

- **Setup** — the event is a draft. You fill in the Setup hub's cards (Details, Registration, Group types, Marks, Staff) and then open registration.
- **Registration** — registration is open and the event hasn't started yet. People sign up through the link you share.
- **Event** — registration has closed or the start date has arrived. Allocation, check-in and rosters take centre stage.

The phase follows from the event's status and dates; you don't set it directly.

### Participant

A person registered to an event. This is the central entity in Moimio — almost every other record (allocation, mark, custom field value, note) hangs off a participant.

Note that a *participant* is different from a *user*. Users are organising-team accounts (admins and staff with login access). Participants are the people attending the event. They are deliberately separate entities — most participants will never log in to anything.

### Registration

The act of a participant signing up for an event, typically through the public registration form. A registration produces a participant record with a `registration_status` of `pending`, `confirmed`, or `cancelled`.

### Confirmation

The transition from `pending` to `confirmed` registration status. It only applies when the event has **Require email confirmation for registration** switched on (it's off by default, in which case registrations are confirmed straight away). Triggered either by the participant clicking a link in their confirmation email, or by an admin confirming on their behalf. By default the allocation engine includes unconfirmed people too; switch off **Include unconfirmed people** in the engine settings to allocate only confirmed ones.

---

## Allocation

### Group type (allocation category)

A way of dividing people up, defined per event. The interface calls it a **group type**; the code and older docs call it an *allocation category*. Two group types — **Room Allocation** and **Small Groups** — are created for every new event, and appear in each reader's own language until you rename them. You can rename, delete, or add to them, and export or import a set of group types as a file. Each group type answers **Can a person be in more than one?**:

- **No, only one** (*exclusive*) — a participant belongs to *one* group in this group type at a time. Rooms are the canonical example.
- **Yes, several** (*overlapping*) — a participant can belong to *several* groups at once. Workshops, sessions, or shifts.

A group type also has a **Name** for its groups (e.g. "Room", "Team").

### Group (allocation unit)

A specific slot within a group type. If "Room Allocation" is the group type, then "Room 3" or "The Lakeview Suite" are groups. The interface says **group**; the code and older docs say *unit*. Each group has an optional capacity, a gender setting (mixed by default), and can optionally be reserved for people carrying one mark (**{mark} only**).

### Allocation

The link between a specific participant and a specific group. The same participant can have multiple allocations (one per group type for "only one" group types, several for "several" ones).

### Capacity

The maximum number of participants a group can hold. Capacity is optional: tick **No capacity limit** (or leave the box empty) and the group accepts any number of people, with its occupancy shown as a plain count. You can still drag someone into a full group by hand; Moimio asks you to confirm the overbooking first.

### Gender restriction

A setting on a group that limits placement to participants of one gender. Three values: **Mixed** (the default — anyone can be placed here), **male only**, **female only**. It applies both to the engine and to manual drag-and-drop. Participants whose gender is unknown cannot be placed in gender-restricted groups.

### Exclusion

Keeping one participant out of one group type while leaving them in every other — for example, someone who lives locally and needs no room but should still be in a small group. Use **Exclude** on the board; the person moves to an **Excluded** list, the engine skips them in that group type, and **Include** puts them back. Assigning an excluded person by hand asks first and lifts the exclusion. Exclusions travel in backups and show in exports.

### Keep as-is (kept group)

A lock on a single group. Click **Keep as-is** and Auto-Allocate won't add anyone to that group or move anyone out of it; click **Kept** to release it.

---

## Allocation engine

### Allocation engine

The deterministic algorithm that proposes a complete allocation for one group type in one shot, given the current participants, groups, and engine settings. Click **Auto-Allocate**, review the **Proposed allocation**, then **Commit allocation** or **Discard**. See [Manual section 6](manual/06-allocation-engine.md) for the full algorithm.

### Pass

The engine works in sequential passes (numbered PASS 1 to PASS 5 in the code). In order: group codes (1); marks, in your priority order (2–3); filling restricted groups (4a) and everyone else (4b); evening out group sizes (4c, the **Even out group sizes** setting) and filling leftover seats (4d); and finally listing anyone unplaced with a reason (5).

### Cluster

Two or more participants the engine should try to keep together — usually because they share a group code (a family or friend group), but sometimes because they share a mark set to **Keep together**. The interface mostly just says "group" here (e.g. "3 groups kept together"). A "cluster of one" (a single participant alone with their group code) is not treated as a cluster; they're placed like any other individual.

### Round-robin

The engine's default placement strategy for individuals (PASS 4b). It walks groups in capacity-ascending order, placing one participant per group per cycle, and skips groups that are full or don't fit the person. Produces a fair fill across the available space. The **Keep the same gender together** setting (on by default) changes the order in which people are taken here, aiming to keep the same gender together where nothing else decides.

### Drain (PASS 4a)

The engine's strategy for restricted groups (limited to one gender, or reserved for one mark). The engine "drains" eligible participants from the remaining pool into each restricted group in turn (smallest capacity first), filling them as fully as possible before moving on to the unrestricted groups. This avoids the classic small-event problem of restricted rooms ending up half-empty.

### Unplaced

A participant the engine could not place. Each one comes with a reason, shown in plain words on the board: too many people share a group code to fit anywhere and splitting is switched off; a group code needs a mixed group and every group is single-gender; the person has no gender on record and every group is restricted to one gender; or every group is full. Admins resolve these by hand. (Excluded participants are not "unplaced"; they're listed separately.)

---

## Group codes and clustering

### Group code

A short human-readable code shared between related registrations to keep them allocated together. Format: `STEM-NNN` (e.g. `SMITH-742`), scoped per event. A family registers with the same group code; the engine treats them as a cluster.

If a registrant doesn't enter a code, Moimio derives the stem from their last name and appends a unique three-digit suffix. If a registrant types only a stem (e.g. `SMITH` without a number), the same applies — a unique suffix is added before saving. This is collision-safe: two unrelated families both typing `SMITH` end up with different codes (`SMITH-742` and `SMITH-883`) and don't accidentally cluster together. A registrant who wants to join an existing cluster types the full code (`SMITH-742`); that's saved verbatim.

The final group code is included in the registration confirmation email so the registrant can share it with anyone else who'd like to be grouped with them.

Group codes apply in every group type where the engine setting **Keep group codes together** is on (the default). **Split group codes if needed** decides what happens when no single group has room for everyone sharing a code: on, they're spread across several groups; off, they're left unplaced for you to handle.

### Exclusive group codes

A per-group-type setting, shown in the engine settings as **A group code takes a whole group to itself**. When on, a group-code cluster *fully claims* the group it lands in — no other participants are placed there even if seats are left over. Useful for dorms and family rooms. Off by default, which suits tables and small groups.

### Cluster behaviour (per-mark)

Set per mark, per group type, in the engine settings. Three behaviours:

- **Keep together** — participants sharing this mark form a sub-cluster (PASS 2). Placed together where possible.
- **Spread evenly** — participants sharing this mark are distributed across groups (PASS 3). One leader per room, that sort of thing.
- **No effect** — the mark is staff-visual only, ignored by the engine.

### Mark priority

The order in which marks are applied (**Apply marks in this order**; drag to reorder, top first). When a participant has more than one mark, only their highest-priority mark drives engine behaviour. Priority and behaviour are configured **per group type in the Engine settings panel** (next to the Auto-Allocate button on the board) — *not* in the mark editor itself. This means the same mark can behave differently in different group types — e.g. "Leader" set to *Keep together* in Room Allocation but *Spread evenly* in Small Groups.

---

## Marks and tagging

### Mark

A colour-coded badge attached to a participant. Free-form — organisers create their own marks per event ("Leader", "First-timer", "Allergic to nuts", "Needs ground floor", "Has guitar"). Visible to staff in the admin UI; never visible to participants.

### Mark assignment

The link between a participant and a mark. A participant can have multiple mark assignments.

### Mark definition

The mark itself: its name, its colour, and which screens it shows on. Defined per event, in the marks editor. (What a mark does in allocation is set per group type; see [Mark priority](#mark-priority).)

---

## Custom fields and check-in

### Custom field

An extra field added to the registration form, beyond Moimio's built-ins. Defined per event using a simple EAV schema. Field types: text, number, select (single choice), boolean (yes/no), date. "T-shirt size", "Dietary requirements", "Have you been before?" are typical examples.

### Check-in field

A custom tick column on the Check-in screen for the day participants arrive. "Arrived", "Picked up welcome pack", "Paid balance in cash", "Signed liability waiver" — anything you'd otherwise track on a clipboard. The Check-in screen can also show registration and custom fields as columns.

---

## People and permissions

### User

An organising-team account with login access. Distinct from a *participant* (a person attending the event). Users have a global role and per-event assignments.

### Role

A user's global authorisation level. Two values: **Super Admin** (`super_admin`, system-wide access; the account made on the first-time setup screen is one) and **Staff** (`staff`, event-scoped, must be assigned to specific events). The previous `event_admin` global role was retired in favour of a per-event role on the assignment record. Two capability flags (`can_manage_users`, `can_create_events`) sit alongside the role and add fine-grained system-level abilities.

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

A free-text memo attached to a participant, an event, a group type or a group. Notes can be **private** (visible only to the author) or **published** (visible to the whole organising team), and show who wrote them. Participants never see notes regardless of state.

---

## Data lifecycle

### Soft delete

The default delete behaviour. Sets a `deleted_at` timestamp on the record; subsequent queries filter it out, but the record physically remains and can be restored. The GDPR data export deliberately includes soft-deleted records — a participant invoking right-of-access *after* asking to be removed is exactly the case where the export must still work.

### Manual erasure

Full physical removal of a record from the database. Moimio v1.0 does not ship a one-click hard-purge UI; for the rare case where regulatory context demands physical removal beyond soft delete, the operation is currently performed as a manual SQL deletion against the soft-deleted record. A first-class hard-purge UI is on the post-1.0 backlog.

### Archive

A reversible "filed away" state for events. Archived events become read-only for everyone except Super Admins, are excluded from the Active and Past tabs of the events list, and are shown in a separate Archived tab; their data stays intact and is still searchable, exportable, and restorable. Different from deletion — and reversible: a Super Admin can unarchive at any time, returning the event to whichever status it was in.

### Participant number

A small per-event integer assigned to each participant on registration. Used in confirmation emails, the participants table, sign-in sheets, and as the human-friendly identifier for preference requests. Not a primary key — Moimio uses UUIDs internally — just a lightweight number for humans.

---

## Integrations

### Outbound webhook

An HTTP POST that Moimio sends to a URL you control, fired the moment a system event happens. Used to connect Moimio to Slack, Zapier, n8n, custom scripts, or any other system that accepts inbound webhooks. Each request is signed with HMAC-SHA256 so receivers can verify it came from Moimio.

Today Moimio sends them when an event is created or deleted and when an allocation is committed. Full integration guide at [`docs/webhooks.md`](webhooks.md).

### Endpoint (webhook)

A configured URL that Moimio sends webhook deliveries to. Each endpoint has a name, a URL, a list of subscribed event types, and a signing secret. Configured in the admin UI under **Webhooks** (Super Admin only). Distinct from an *event* in the Moimio sense — an endpoint receives notifications about events.

### Signing secret

A random string generated server-side when a webhook endpoint is created. Used to compute the HMAC-SHA256 in the `Moimio-Signature` header of every outbound delivery. Shown to the admin exactly once at creation in a sticky modal; never recoverable through the UI afterwards. If lost, generate a new one via the **Rotate secret** action.

### Delivery

A single attempt to send a webhook event to an endpoint. Recorded in the `outbound_webhook_deliveries` table with status, response code, duration, and any error. The last 50 deliveries per endpoint are visible in the admin UI; the full log is kept for the retention window (default 30 days) before the daily prune job removes old rows.

### Endpoint state

A health indicator on each webhook endpoint: **Active** (healthy), **Degraded** (5 consecutive failures), **Disabled** (20 consecutive failures, requires **Re-enable**), or **Paused** (switched off by an admin with **Pause**, back on with **Resume**). Apart from pausing, transitions are driven by delivery outcomes.

### Private targets

Webhook addresses on private, loopback or link-local networks (`10.x`, `192.168.x`, `localhost`, `169.254.169.254` and similar). Moimio refuses them, both when the endpoint is saved and again before every delivery, so a webhook can't be used to reach machines only the server can see. A self-hoster whose receiver is on their own network can allow them with `WEBHOOK_ALLOW_PRIVATE_TARGETS=true`.

### SaaS-managed endpoint

A webhook endpoint that was auto-registered at container startup via the `MOIMIO_WEBHOOK_URL` and `MOIMIO_WEBHOOK_SECRET` environment variables. Flagged `managed_by="saas"` in the database and hidden from the admin UI. This is how automated deployment platforms wire a Moimio container to a central event receiver without an admin having to configure it by hand. If you manage your own endpoints, leave these two environment variables empty and the flag never appears.

---

## Documentation conventions

### "v1.0", "v0.x"

`v1.0` is the first public release. Earlier `v0.x` references in the source code, commit messages, and internal documentation correspond to development iterations leading up to v1.0; they are not separate published releases. Releases since then are tagged like `v1.0.6`; the [changelog](../CHANGELOG.md) lists them.

### "The engine"

Throughout the docs, "the engine" without qualification means the allocation engine. It's the only engine in Moimio.

### "The board" / "AllocationBoard"

The drag-and-drop screen for reviewing and adjusting an allocation, opened from **Organise** in the event's menu by picking a group type. It shows each group, the **Unassigned** panel (which can be docked or floated), the **Excluded** list, and the **Auto-Allocate** and **Engine settings** buttons.

### "InsightPanel"

A slide-in panel, titled **Participant profile**, that shows everything Moimio holds about a single participant — registration data, marks, allocations, notes, audit history. The InsightPanel is reachable via the **(i)** icon next to a participant's name in the **AllocationBoard** (Organise page) or the **Check-in panel**. It is **not** opened from the People page (the People page focuses on table operations and inline editing).
