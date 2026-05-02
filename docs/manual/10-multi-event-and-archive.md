# 10 — Multi-event & archive

Moimio is built around the assumption that an organisation runs more than one event. Once you've configured a registration form, allocation categories, and a staff team, you'll often want to reuse that setup. This section covers how to run multiple events from one Moimio instance, how archiving works, and how to duplicate an event configuration.

---

## The events list

Sidebar → **All Events** → the list view at `/admin`.

Three tabs at the top:

- **Active** — events with status `open` (registration is collecting) or `closed` (registration done; running or upcoming).
- **Past** — events whose end_date is in the past.
- **Archived** — events explicitly archived (covered below).

Each row: event name, status badge, dates, participant count, and a **⋯** menu on the right with per-row actions (duplicate, archive, etc.).

The **+ New Event** button at the top creates a fresh event. **↑ From backup** restores an event from a backup zip (see [§09](09-data-export-gdpr.md#backups-and-event-level-export)).

---

## Status vs archive — orthogonal concepts

A common point of confusion. There are two independent dimensions:

- **Status:** `draft` → `open` → `closed`. Lifecycle of an event: configuring → registration is live → registration is done. This is the natural progression of a single event.
- **`is_archived`:** boolean flag, defaults false. Whether the event is "filed away" — read-only, hidden from active views, but its data is still there.

**An event can be in any status AND archived simultaneously.** A draft event you abandoned can be archived. A live event can be archived (which freezes it). A closed event can be archived (the typical case — you ran the event, it's done, you want it tucked away).

Archive is **reversible**. Unarchive at any time and the event returns to whichever status it was in.

---

## Archiving an event

### Where the button is

**Setup hub → Danger zone → Archive this event** (admin only) OR **Event details → Danger zone → Archive this event** (Super Admin only).

The Danger zone section is collapsed by default to reduce accidental clicks; click the burgundy header to expand.

### What happens when you archive

- The event moves to the **Archived** tab in the events list.
- The event becomes **read-only for everyone, including Super Admins**. (To edit, you must unarchive first.)
- The public registration form returns an "event is archived" error if anyone tries to register.
- Existing data — participants, allocations, check-ins, notes — stays intact.
- An archived banner appears at the top of every page within the event.

### Who can archive

By default, **Super Admin** only via the Event details Danger zone. Per-event admins can archive too via the Setup hub Danger zone (depending on the event's phase). Staff users cannot.

### Unarchiving

Same path: **Danger zone → Unarchive this event**. The event returns to its previous status. Registration accepts new entries again (if status is `open`); check-ins resume; the event reappears in Active or Past.

---

## Duplicating an event

When you're running a recurring event — same registration form, similar group types, returning staff — duplicating an existing event saves an enormous amount of setup.

### How to do it

Events list → ⋯ menu on the source event row → **Duplicate**. A modal opens.

### What gets copied (configuration only)

- **Event name** — pre-filled with `{original} (copy)`. Editable.
- **Registration form** — every field (built-in + custom).
- **Group types** — every allocation category and its units (capacity, gender restriction, etc.).
- **Marks** — every mark definition (name, colour, visibility settings).
- **Staff admins** — every per-event admin assignment.

### What does NOT get copied

- **Participants** — registration data is per-event by design.
- **Allocations** — depend on participants.
- **Check-ins** — depend on participants and time.
- **Notes** — typically operational, not template-able.

The copy lands as a fresh draft event, ready to open registration when you're ready.

### What about backups

Backups (covered in [§09](09-data-export-gdpr.md#backups-and-event-level-export)) are the alternative path — they preserve everything including participants. **Use Duplicate when starting a new run; use Backup when migrating between deployments or making a snapshot of an in-progress event.** Backups also offer a "structure-only" mode that's effectively a duplicate.

---

## Running multiple events in parallel

Nothing in Moimio prevents this. Each event is its own world: its own participants, its own allocation categories, its own staff assignments. Cross-event participant overlap (the same person registering for two events) is treated as two independent registrations — one per event — because the registration form per event differs.

Practical things to know:

- **Sidebar context.** When you're inside an event, the sidebar shows that event's controls. Switch via the **Events** link at the top of the sidebar (visible to all roles since v0.81).
- **Staff assignments are per-event.** A staff member assigned to Event A doesn't automatically have access to Event B. Re-assign for each event.
- **Custom fields are per-event.** Event A's "T-shirt size" custom field is a different DB row from Event B's "T-shirt size", even if the labels match.
- **Allocation categories are per-event.** The "Rooms" category in Event A has nothing to do with the "Rooms" in Event B.

This isolation is intentional. It means you can confidently run a women's retreat and a men's conference from the same Moimio without any data crossing.

---

## What's next

[Section 11 — Staff & permissions](11-staff-permissions.md) covers the staff role model, per-event assignments, and the granular permissions for People, Organise, Check-in, Reports, and Marks.
