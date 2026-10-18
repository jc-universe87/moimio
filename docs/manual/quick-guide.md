# Quick Guide

This is the speed-run version of the manual. One event, beginning to end. Skip the detail, get to the PDF.

If you want the *why* behind anything here, the numbered sections (`01-...` through `11-...`) cover the same ground at depth.

---

## The mental model

Every event in Moimio moves through three phases:

1. **Setup** — you configure everything. The public registration form is not yet taking sign-ups.
2. **Registration** — the form is live; participants sign up; you watch the count go up.
3. **Event** — registration is closed (or the start date has arrived); allocations are confirmed; check-in begins; the event happens.

The admin sidebar changes per phase. In Setup it shows a single **Setup** link to the Setup hub; in Registration it shows **Registration**, **Organise**, **People** and **Reports**; in Event it shows **Organise**, **People** and **Reports**, with check-in one click away from Organise. Occasional settings sit in a **More** menu. You don't need to learn this — the sidebar rearranges itself.

---

## Step 1 — Create the event

From the events list (the page you land on after signing in), click **+ New Event**. The form is deliberately minimal:

- **Event name** — what participants will see at the top of the registration form.
- **Transfer settings from another event** (optional) — tick it, pick a past event and choose what to copy: marks, registration form, custom fields, group types and team members. Participants are never copied.

Click **Create event**. The event is created as a draft. Unless you transferred group types, two are already in place: **Room Allocation** and **Small Groups**. You land on the **Setup hub** in **Setup phase**.

---

## Step 2 — Fill in the event details

The Setup hub has five cards. Open the **Details** card first.

Fill in:

- **Event name** — already filled in; change it if you like.
- **Description** (optional) — a sentence or two for participants. Shows on the registration form.
- **Location** — where the event is.
- **Start Date** and **End Date** — when the event happens. On the start date the event moves from Registration to Event phase by itself; after the end date it counts as **Done**.
- **Timezone** — starts as the timezone in your Preferences.

Click **Save & confirm**. That's one of the two cards you must confirm before opening registration.

---

## Step 3 — Configure the registration form

Open the **Registration** card.

First Name, Last Name, Email and the consent checkbox are always on the form. Under **Built-in Fields** you can add **Gender**, **Date of Birth**, **Phone**, **Address**, **Country** and **Church / Organisation**, each with a **Show** and a **Required** checkbox.

Add custom fields if you need anything else: click **+ Add Field**, give it a label, choose the type (**Text**, **Number**, **Dropdown**, **Yes/No** or **Date**), then **Add Custom Field**. Examples that come up often:

- "T-shirt size" (Dropdown: S, M, L, XL)
- "Are you a small-group leader?" (Yes/No)
- "First time at this event?" (Dropdown: Yes, No)
- "Dietary requirements" (Text)

The form also always has a **Coming with family or friends?** section for group codes, and a **Message to Organisers** box.

Click **Save & confirm** at the bottom of the card. That's the second card you need.

---

## Step 4 — Set up your group types

Open the **Group types** card. **Room Allocation** and **Small Groups** are already there.

You can rename them (pen icon), delete them (bin icon), or click **+ Add group type** to add more. For example, a **Workshops** type where the answer to **Can a person be in more than one?** is **Yes, several**, so people can attend several workshops.

The actual rooms and groups inside each type are added later, from **Organise**. The card counts as done as long as at least one group type exists.

---

## Step 5 — Open registration

At the bottom of the Setup hub, once **both** Details and Registration are confirmed, the button changes to **Ready to open registration →**. Click it.

The event is now open and you're in **Registration phase**. The public registration form is live.

Click **Share form** at the top of the **Registration** page to get the link, a QR code and a **Copy** button. Send it to your participants — email, WhatsApp, parish bulletin, however you reach them.

Optional, but do it now if you want it: **More ▸ Registration form ▸ Email confirmation** lets you require participants to confirm their email address (it's off by default) and send yourself a test email.

---

## Step 6 — Watch registrations come in

The **Registration** page shows live counts, a sign-up chart and the most recent sign-ups. The **People** page lists everyone. Each person has a status:

- **Confirmed** — registered (and, if you switched on email confirmation, clicked the link), or confirmed by you.
- **Pending** — only when email confirmation is on: registered but hasn't clicked the email link yet.
- **Cancelled** — cancelled, by them or by you.

By default the allocation engine only places **confirmed** people (there's an **Include unconfirmed people** setting if you need it). On the People page you can:

- Click a cell (name, email, group code, phone, etc.) to edit it in place.
- Change someone's status from the status pill on their row — useful when an email never arrived and you want to confirm them by hand. **Resend** sends their registration email again.
- Click **Notes** on a row to add a note about that person, private or shared with the team.
- Click **↓ Export data** on a row to download everything Moimio holds about that person (their personal data export).
- Add **marks** — colour-coded labels like "Leader" or "Needs ground floor" — using the small mark icon next to a participant's name (in People, on the allocation board, or at check-in).

---

## Step 7 — Run the allocation engine

When you're ready to allocate (usually after registration closes, but you can try it earlier as a draft), go to **Organise**.

Organise shows one card per group type. Open a group type, add its rooms or groups if you haven't yet, then click **Auto-Allocate**. You'll be asked which **Allocation mode** to use:

- **Allocate new participants only** — keeps existing placements and only places people who aren't placed yet. Use this when you've placed some people by hand and want the engine to fill in around them.
- **Reallocate everyone from scratch** — clears this group type's placements and starts over. Use this after changing engine settings or marks.

The engine then works through its settings in this order (you'll find them under **Engine settings**):

1. **Include unconfirmed people** — off by default.
2. **Keep group codes together** — people sharing a group code are placed together (with **Split group codes if needed** for codes too big for any one group, and **A group code takes a whole group to itself** for family rooms).
3. **Apply marks in this order** — each mark keeps its holders together or spreads them evenly, as you set it.
4. **Keep the same gender together**.
5. **Even out group sizes**.

Capacity and groups restricted to one gender are never broken.

The result is a **Proposed allocation** — nothing is saved yet. You see who would go where and anyone the engine couldn't place, with a reason.

If the proposal isn't right:

- **Change the settings** and **Auto-Allocate** again with **Reallocate everyone from scratch**.
- **Drag specific people** to where you want them, then **Auto-Allocate** with **Allocate new participants only** — the engine fills in around your choices.
- **Keep as-is** on a room or group locks it, so Auto-Allocate leaves it alone.
- **Exclude** keeps someone out of this one group type (for example, a day guest who needs no room) while they stay in all the others.
- Or just drag people between groups yourself. The engine proposes; you decide.

When you're happy, click **Commit allocation** (or **Discard** to throw the proposal away). Once everyone is placed, **Confirm group type** marks it as finished; any later change reopens it automatically. Every move is recorded in the history, so you can always see who was moved where, and by whom.

---

## Step 8 — Generate rosters

Go to **Reports**. Under **Roster downloads**, each group type has two buttons:

- **Compact** — a short list per group. Good for clipboards and doors.
- **Sign-in** — a printable sheet with checkboxes for check-in staff.

The **PDF language** dropdown above them sets the language of every roster on the page (separately from your own interface language), and **Include cover page** adds a front page with the event's details and numbers. For raw participant data as a spreadsheet file, use the **↓ Export ▾** button on the **People** page.

---

## Step 9 — Check people in on the day

Once the start date arrives, the event is in Event phase, sub-state **Live**. Open **Organise** and click **Enter check-in mode →** at the top right (admins). Staff members with check-in access see **Check-in** as its own item in the sidebar.

Click **+ Create column** to set up the tick-off columns you want (Payment, T-Shirt, Name Badge…). You can do this on the day or beforehand. Then tick people off as they arrive.

Check-in works well on a tablet or phone, and several people can check in at once on different devices — the ticks appear on everyone's screen straight away.

---

## Step 10 — After the event

Once the end date has passed, the event is in Event phase, sub-state **Done**, and moves to the **Past** tab of the events list. You can:

- Close registration if you haven't already — use the **Close registration** button on the **Registration is still open** banner at the top of **Organise**.
- Download a backup for safe keeping under **Manage ▸ Backup** (Super Admins).
- Archive the event (Super Admins): the **⋯** menu on the events list, or **More ▸ Event details ▸ Danger zone ▸ Archive**. Archived events are read-only. It's reversible with **Unarchive**.
- Reuse its setup for next year: click **+ New Event**, tick **Transfer settings from another event** and pick this one. Group types, custom fields, marks and more come across; participants don't.

---

That's the full flow. Each numbered section in this manual covers one of the steps above in more depth — including edge cases, gotchas, and the underlying model.
