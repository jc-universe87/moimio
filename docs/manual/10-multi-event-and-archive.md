# 10 — Multi-event & archive

Moimio is built around the assumption that an organisation runs more than one event. Once you've configured a registration form, group types and a team, you'll often want to reuse that setup. This section covers running several events from one Moimio, how archiving works, and how to start a new event from a past one.

<p align="center">
  <img src="../assets/events-list.png" alt="The events list with the Active, Past and Archived tabs, event cards with phase badges, and the + New Event and From backup buttons" width="720">
  <br>
  <em>The events list</em>
</p>

---

## The events list

Sidebar ▸ **Events**. When you're inside an event, use **All Events** at the top of the sidebar to get back here.

A search box sits at the top, then three tabs, each showing a count:

- **Active** — events that aren't archived and haven't ended yet (including events with no dates set). Pinned events appear first.
- **Past** — events whose end date has passed.
- **Archived** — events that have been archived (covered below). Super Admins always see this tab; others see it only when it has something in it.

Each card shows the event name, a badge for where it is (**Setup**, **Registration**, **Event**, **Past** or **Archived**), its dates and location, and a headline number such as how many are registered. Super Admins also get a **⋯** menu on each card with **Pin to top** / **Unpin**, **Archive** / **Unarchive**, and **Delete event**.

The **+ New Event** button creates a fresh event. **↑ From backup** takes you to the Backup page to restore an event from a backup file (see [§09](09-data-export-gdpr.md#backups)). Both buttons are shown to Super Admins and to team members who have been given **Can create new events**.

---

## Closing registration vs archiving

Two different things, often confused:

- **Closing registration** is part of an event's normal life: Setup → Registration → Event. Closing stops new sign-ups and moves the event on to the Event phase, where you allocate and check people in. See [§02](02-events-and-registration.md).
- **Archiving** files an event away. It becomes read-only and moves to the **Archived** tab, but all its data is kept.

An event can be archived at any point — a draft you abandoned, or (the usual case) an event that's over and you want tucked away. Archiving is **reversible**.

---

## Archiving an event

### Where the button is

Archiving is for **Super Admins**. Any of these work:

- Events list ▸ **⋯** on the event's card ▸ **Archive**
- **Setup hub ▸ Danger zone ▸ Archive** (while the event is still in Setup)
- **Event details ▸ Danger zone ▸ Archive**

The Danger zone is collapsed by default to avoid accidental clicks — click its header to open it. Confirm with **Archive** in the **Archive this event?** dialog.

### What happens when you archive

- The event moves to the **Archived** tab in the events list.
- The event becomes **read-only for everyone, including Super Admins**. To change anything, unarchive it first.
- The public registration form refuses new sign-ups.
- Existing data — participants, allocations, check-ins, notes — stays intact.
- An **Archived** banner appears at the top of the event's pages.

### Unarchiving

Same places: **⋯ ▸ Unarchive** on the card, or **Danger zone ▸ Unarchive**. The event becomes editable again and reappears in **Active** or **Past**, depending on its dates. Registration and check-in carry on where they left off.

---

## Starting a new event from a past one

When you run a recurring event — same registration form, similar rooms, the same team — copying the setup from last time saves a lot of work.

### How to do it

1. Events list ▸ **+ New Event**.
2. Type the new event's name.
3. Tick **Transfer settings from another event** and choose the event to copy from.
4. Under **What to copy**, untick anything you don't want. All five are ticked to start with:
   - **Marks** — the mark definitions (name, colour and so on), not who carried them.
   - **Registration form** — which standard fields are shown and required.
   - **Custom fields** — your own questions.
   - **Group types** — every group type with its groups, capacities and gender settings. Groups restricted to a mark are linked to the new event's copy of that mark; if you don't copy marks, those restrictions are dropped.
   - **Team members** — everyone on the old event's team, with the same role and permissions.
5. Click **Create event**.

The new event starts in Setup, ready for you to add dates and open registration. **No participant data is ever copied** — no participants, allocations, check-ins or notes.

You can only copy from events you have access to.

### Copying between installations

To carry setup to a different Moimio, or to an event that already exists, export pieces as files: **Export group types** / **Import group types** on the allocation side (see [§05](05-group-types-and-units.md)) and **Export form** / **Import form** for the registration form (see [§02](02-events-and-registration.md)). These files hold configuration only, never personal data.

### What about backups

Backups (see [§09](09-data-export-gdpr.md#backups)) are the other route — a full backup keeps everything, including participants. **Copy settings when starting a new run; use a backup as a safety copy or to move an event to another Moimio.** A **Structure only (GDPR-safe)** backup is a shareable template with no personal data.

---

## Running multiple events in parallel

Nothing in Moimio prevents this. Each event is its own world: its own participants, its own group types, its own team. The same person registering for two events is treated as two separate registrations — one per event.

Practical things to know:

- **Switching events.** Use **All Events** at the top of the sidebar, then pick another event. Every role sees this link.
- **Team access is per event.** A team member on Event A doesn't automatically get access to Event B. Add them to each event (or copy **Team members** when creating the new one).
- **Custom fields are per event.** Event A's "T-shirt size" question is separate from Event B's, even if the wording matches.
- **Group types are per event.** "Room Allocation" in Event A has nothing to do with "Room Allocation" in Event B.

This separation is intentional. You can run a women's retreat and a men's conference from the same Moimio without any data crossing.

---

## What's next

[Section 11 — Staff & permissions](11-staff-permissions.md) covers user accounts, each event's team, and the permissions for People, Organise, Check-in, Reports and Marks.
