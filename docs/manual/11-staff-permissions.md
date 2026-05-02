# 11 — Staff & permissions

Moimio has two global roles and per-event assignments. This section covers both: who's a Super Admin, who's Staff, and how to grant Staff access to specific events with the right permissions.

<!-- TODO: screenshot at docs/assets/staff-permissions.png — Staff & permissions assignment form showing User picker, Role dropdown, and the five permission surfaces -->

---

## Two global roles, plus per-event assignments

### Super Admin (global)

A user account with `role: super_admin`. Created at first install via the on-screen wizard, and addable via Users management thereafter. Super Admins:

- Have full access to every event in the instance.
- Can create new events.
- Can manage users (create, edit, deactivate).
- Can archive / unarchive any event.
- Are the only role allowed in the **Danger zone** of Event details.

There's no per-event configuration for Super Admin — the global role grants global access.

### Staff (global)

A user account with `role: staff`. By itself, **a Staff account has no access to anything.** Each event needs an explicit assignment with a per-event role and permission set. A Staff user with no assignments sees a "waiting for your first assignment" placeholder when they log in.

This separation matters: a Staff account is just a login. The actual access is decided per-event by the Super Admin or that event's admins.

---

## Per-event assignments

For every event, there's a list of assigned users. Each assignment has:

- **A role within this event:** `event_admin` or `staff`.
- **A permissions object** (only relevant when the role is `staff`).

You manage assignments from the **Setup hub → Staff card** during Setup phase, or **More → Staff & permissions** during later phases. Both reach the same component.

### Event Admin role

An assignment with role `event_admin` grants the user full access to *this specific event*, equivalent to a Super Admin's view of that one event. They can:

- Edit event details and configuration.
- Open and close registration.
- Manage allocations.
- Run the engine, commit allocations.
- Access check-in.
- Create / edit / delete marks.
- Export reports and data.
- Assign other Staff to this event.

The permissions object is **ignored** for event_admins — full access is implicit.

### Staff role

An assignment with role `staff` grants only the views explicitly listed in the permissions object. The five permission surfaces are described below.

---

## The five permission surfaces

Each surface is independent of the others. A Staff user can have any combination — read access to People + write access to Marks, for example, or only Reports access.

### People (read / write / none)

The People table, the registration data, and per-row participant exports.

- **Read** — sees the participant list, can search, filter, view details.
- **Write** — can edit fields, change registration status, soft-delete participants.
- **None** — sidebar item hidden.

### Organise (read / write / none)

The AllocationBoard and engine settings.

- **Read** — sees allocations across all categories.
- **Write** — can drag-and-drop, run the engine, commit allocations, edit category settings.
- **None** — sidebar item hidden.

### Check-in (checkbox + optional sub-toggle)

The Check-in panel. The primary checkbox grants the Staff member access to view the check-in list and tick people in once the event begins.

When the primary checkbox is ticked, a sub-toggle appears: **Access before the event starts**. When this is also ticked, the Staff member gets access to the Check-in panel during the Registration phase (via the **→ Set up the check-in panel** link on the Registration overview page) and can add or edit check-in columns ahead of arrivals. Useful for events where a designated coordinator — not always an event admin — handles check-in setup.

Read-only access isn't separately offered. Checking people in is the whole point of the surface; the sub-toggle gates the timing of access, not the level.

Admins (Super Admin and event-admin role on the assignment) always have full check-in access including the pre-event capability — they don't see the sub-toggle because it's implicit.

### Reports (checkbox)

The Reports page (dashboard tiles + roster downloads).

- **Checked** — sees the dashboard, can download Compact and Sign-in PDFs.
- **Unchecked** — sidebar item hidden.

The **Detailed** PDF format requires `people: read` because it includes PII; reports access alone is not sufficient for it.

### Marks (checkbox)

Whether the Staff member can create marks, edit/delete marks they created, and assign marks to participants.

- **Checked** — sees a Marks item in the sidebar; can create new marks; can edit/delete marks they personally created (not marks created by others); can assign/unassign marks on participants in the InsightPanel.
- **Unchecked** — no Marks sidebar item.

**Read access to marks is implicit with event access.** Anyone who can see participants in any view also sees the marks already assigned to them — they can click a mark dot to see what it means. The marks permission specifically gates *write* (creation + assignment) operations.

---

## Assigning a Staff member to an event

From the Setup hub or More menu's Staff card:

1. Click **+ Assign user**.
2. Pick a user from the dropdown (only users with role `staff` appear; Super Admins manage their own access globally).
3. Pick a role: `event_admin` or `staff`.
4. If `staff`: configure the five permission surfaces.
5. Click **Assign user**.

### Copy permissions from existing

When you have an event with several Staff assignments, the **Copy permissions from** dropdown speeds up adding new staff with the same access pattern. Pick an existing assignment; the new form pre-fills with that pattern's permissions. You can then adjust before saving.

---

## Editing or removing an assignment

In the Staff card list, each assignment row has Edit / Remove buttons.

- **Edit** — same form as Assign, populated with the current values. Save updates the role / permissions.
- **Remove** — confirmation prompt, then the assignment is deleted. The user account isn't touched — they just lose access to this specific event.

If a Staff user is currently looking at the event when their assignment is removed, their next page interaction will fall through to a "no access" placeholder.

---

## Deactivating a user vs removing an assignment

Two different scopes:

- **Remove an assignment** → revokes access to *one* event. The user keeps their login and their other assignments.
- **Deactivate a user** (Super Admin only, in Users management) → disables the login entirely. They can't sign in. All their assignments become moot.

Deactivation is the right path for a Staff user leaving the organisation. Assignment removal is the right path for "she's done with this event but still on next year's team."

---

## Audit trail

Every assignment change (create, edit, remove) emits a structured log entry. Every Staff action that mutates data (drag a participant, tick a check-in, create a mark) emits its own audit log entry tagged with the actor's user_id. Available in `docker compose logs backend`.

For per-participant exports specifically, the audit history visible in the export does **not** include the actor's user_id (see [§09](09-data-export-gdpr.md) — that's a deliberate Article 15 scoping decision). Internal admin logs do retain the actor identity.

---

## What's next

That's the end of the user manual. For more:

- [Glossary](../glossary.md) — Moimio-specific terms.
- [FAQ](../faq.md) — common questions.
- [GDPR compliance](../gdpr-compliance.md) — privacy posture and architectural details.
- [Data model](../data-model.md) — schema reference for developers and integrators.
