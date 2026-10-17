# 11 — Staff & permissions

Moimio has two kinds of user account and a team for each event. This section covers both: who's a Super Admin, who's Staff, and how to give people access to a specific event with the right permissions.

<p align="center">
  <img src="../assets/staff-permissions.png" alt="The Assign user to event form showing the User picker, the Role dropdown, Copy permissions from, and the five permission settings" width="560">
  <br>
  <em>Adding someone to an event's team</em>
</p>

---

## User accounts

Accounts are managed at Sidebar ▸ **Users** (under **Manage**), on the **User Management** page.

### Super Admin

The first Super Admin is created during first-time setup. More can be added from **User Management** — only a Super Admin can make someone else a Super Admin. Super Admins:

- Have full access to every event.
- Can create events, and manage users.
- Are the only ones who can archive, unarchive, delete or pin events, and restore backups.
- Are the only ones who see **Backup**, **Workspace** and **Webhooks** in the sidebar.

Super Admins don't need to be added to an event's team — they already have access everywhere.

### Staff

A **Staff** account is just a login. **On its own, a Staff account has no access to any event.** Access comes from being added to an event's team, with a role and permissions for that event. A Staff user who isn't on any team yet sees a **Waiting for your first assignment** screen when they sign in.

Two extra capabilities can be ticked for any Staff user:

- **Allow this admin to manage users** — they can open **User Management** and create, edit, deactivate and delete Staff accounts (but not Super Admins).
- **Can create new events** — they get the **+ New Event** button. Whoever creates an event automatically becomes its Event Admin.

### Adding, editing and removing accounts

- **+ New User** opens the form: **Full name**, **Email**, **Password**, **Role**, and the two capabilities. Click **Create User**.
- In the list, the grey pen edits a user's name, role and capabilities.
- **Deactivate** stops someone signing in without deleting anything. **Reactivate** lets them back in.
- The red trash icon deletes the account for good (**Delete permanently**). You can't delete yourself.

**Deleting a user always works, whatever they did in Moimio.** Their places on event teams go with them, and so do their unpublished (draft) notes. Notes they published stay, and are shown as written by **[removed user]**. Their entries in the allocation history stay too, also shown as **[removed user]**.

Deactivate is the gentler choice if you're unsure — it can be undone; deleting can't.

---

## Each event's team

Every event has its own list of team members. Each has:

- **A role for this event:** **Event Admin** or **Staff**.
- **Permissions** (only used when the role is Staff).

Manage the team from the **Setup hub ▸ Staff** card during the Setup phase, or **More ▸ Staff & permissions** once registration has opened. Both open the same **Staff & permissions** panel.

To add people you need to be a Super Admin, or have **Allow this admin to manage users** — the list of people to choose from comes from User Management. Someone must have an account before they can be added.

### Event Admin role

**Event Admin** gives full access to *this one event*. They can:

- Edit event details, the registration form and group types.
- Open and close registration.
- Run the allocation, commit results and keep people out of a group type.
- Use check-in, including setting it up before the event.
- Create, edit and delete marks.
- Download reports and exports, including a participant's personal data export.
- Remove participants.
- Manage the event's team (with the user-management capability, see above).

Archiving, deleting and restoring events stay with Super Admins. For Event Admins the permission settings are ignored — full access is implied.

### Staff role

**Staff** on an event can do only what their permissions allow. The five permission settings are described below.

---

## The five permission settings

Each setting is independent. A Staff member can have any combination — for example, read-only People plus Marks, or only Reports.

### People access (No access / Read only / Read & write)

The People table and registration details.

- **Read only** — sees the participant list; can search, filter and view details.
- **Read & write** — can also edit details, change status and group codes, register people, and assign marks.
- **No access** — the People item is hidden.

Removing participants and personal data exports are for Event Admins only.

### Organise access (No access / Read only / Read & write)

The allocation board.

- **Read only** — sees who is in which group, in every group type.
- **Read & write** — can drag people between groups, and add, edit or remove groups.
- **No access** — the Organise item is hidden.

Running the allocation, committing it, changing group type settings and keeping people out of a group type are for Event Admins.

### Check-in access (checkbox + optional extra)

The primary checkbox lets the Staff member view the check-in list and tick people in once the event begins.

When it's ticked, a second option appears: **Access before the event starts**. With this, they can open check-in during the Registration phase, before the event starts, and tick people in early, for example to record who has already paid. Adding, renaming or deleting check-in columns stays with Event Admins and Super Admins, even though the hint under the checkbox suggests otherwise.

There's no read-only check-in: ticking people in is the whole point. The extra option controls *when* they get access, not how much.

Super Admins and Event Admins always have full check-in access, including before the event.

### Reports access (checkbox)

The Reports page.

- **Ticked** — sees the reports and can download the Compact and Sign-in roster PDFs.
- **Unticked** — the Reports item is hidden.

The **Detailed** roster and the participant spreadsheet contain personal details, so they also need **People access** — Reports access alone isn't enough.

### Marks access (checkbox)

- **Ticked** — sees a Marks item in the sidebar; can create marks, edit or delete marks *they* created (not other people's), and assign marks to participants.
- **Unticked** — no Marks item.

**Everyone with access to the event can see marks.** Anyone who can see participants can click a mark to see what it means. Marks access is about creating and assigning them. (People **Read & write** also allows assigning marks.)

---

## Adding someone to an event

From the **Staff** card or **Staff & permissions**:

1. Click **+ Assign user**.
2. Under **User**, choose someone (**Pick a user**). The list shows active accounts that aren't already on this event.
3. Choose a **Role**: **Staff** or **Event Admin**.
4. For Staff, set the five permissions.
5. Click **Assign user**.

### Copy permissions from

When the event already has Staff members, **Copy permissions from** lets you fill the form with someone else's settings (**Select a staff member**). Adjust anything before saving.

Tip: when creating next year's event, you can copy the whole team across — see [§10](10-multi-event-and-archive.md#starting-a-new-event-from-a-past-one).

---

## Editing or removing someone from an event

Each team member's row has a grey pen and a red trash icon.

- **Edit** (pen) — same form, filled in with their current role and permissions. Click **Save**.
- **Remove** (trash) — confirm in **Remove user from event?** Their access to this event ends. Their account isn't touched — they keep any other events.

If someone is looking at the event when they're removed, their next click shows a "no access" screen.

---

## Deactivating a user vs removing them from an event

Two different scopes:

- **Remove from an event** → ends access to *one* event. They keep their login and their other events.
- **Deactivate a user** (in User Management) → they can't sign in at all. Their team places stay on record but can't be used.

Deactivate when someone leaves the organisation. Remove from an event when "she's done with this event but still on next year's team."

---

## Keeping track

The history in each participant's profile panel (the **ⓘ View profile** icon) shows who placed or moved them, and when. Key admin actions — creating, archiving and deleting events, removing participants, personal data exports — are also written to the server log (`docker compose logs backend` on a self-hosted install).

A participant's own data export leaves out which team member made each move (see [§09](09-data-export-gdpr.md)).

---

## What's next

That's the end of the user manual. For more:

- [Glossary](../glossary.md) — Moimio-specific terms.
- [FAQ](../faq.md) — common questions.
- [GDPR compliance](../gdpr-compliance.md) — privacy posture and architectural details.
- [Moving a workspace to your own Moimio](../moving-a-workspace.md) — moving every event to a server you run.
- [Data model](../data-model.md) — schema reference for developers and integrators.
