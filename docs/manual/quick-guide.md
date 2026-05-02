# Quick Guide

This is the speed-run version of the manual. One event, beginning to end. Skip the detail, get to the PDF.

If you want the *why* behind anything here, the numbered sections (`01-...` through `11-...`) cover the same ground at depth.

---

## The mental model

Every event in Moimio moves through three phases:

1. **Setup** — you configure everything. The public registration form is not yet live.
2. **Registration** — the form is live; participants sign up; you watch the count go up.
3. **Event** — registration is closed; allocations are confirmed; check-in begins; the event happens.

The admin sidebar changes per phase. In Setup it lands on a single Setup hub; in Registration it surfaces People, Organise, and Reports; in Event the same plus a one-click path into Check-in mode from Organise. You don't need to learn this — the UI re-arranges itself.

---

## Step 1 — Create the event

From the events list (the page you land on after login), click **+ New event**. The form is deliberately minimal:

- **Name** — what participants will see at the top of the registration form.
- **Copy marks from another event** (optional) — useful when you've used Moimio before and want to reuse your mark definitions.

Save. The event is created in `draft` status with two default categories (**Rooms** and **Small Groups**) already in place. You land on the **Setup hub** in **Setup phase**.

---

## Step 2 — Fill in the event details

The Setup hub has five cards. Open the **Details** card first.

Fill in:

- **Start date** and **end date** — when the event happens. The start date determines when you auto-shift from Registration to Event phase; the end date determines when Event phase shifts to its **Done** sub-state.
- **Location** — where the event is.
- **Timezone** — defaults to your user preference.
- **Description** (optional) — a paragraph or two of context for participants. Plain text. Shows on the registration form.

Click **Save & confirm**. This sets the `details_confirmed` flag — one of two gates you need to pass before opening registration.

---

## Step 3 — Configure the registration form

Open the **Registration** card.

The built-in fields you can toggle are: **Gender**, **Date of birth**, **Phone**, **Address**, **Country**, **Church / Organisation**. Email and full name are always on. For each toggleable field you set whether it's shown and whether it's required.

Add custom fields if you need anything beyond the built-ins. Click **+ Add Field**, choose the type (text / number / select / boolean / date), give it a label. Examples that come up often:

- "T-shirt size" (select: S / M / L / XL)
- "Are you a small-group leader?" (boolean: Yes / No)
- "First time at this event?" (select: Yes / No)
- "Allergies and special needs" (text)

Click **Save & confirm** at the bottom of the card. This sets the `registration_confirmed` flag.

---

## Step 4 — Set up your group types

Open the **Group types** card. Two categories — **Rooms** and **Small Groups** — are already there as defaults.

You can rename the defaults, delete them if you don't need them, or add more categories alongside. For example, a **Workshops** category with overlapping rule type, where participants can attend several workshops.

The card is marked done as long as at least one category exists.

---

## Step 5 — Open registration

Back at the Setup hub: when **both** Details and Registration cards are confirmed, an **Open registration** button appears at the bottom.

Click it. The event status flips from `draft` to `open`. You're now in **Registration phase**. The public registration link is live.

Find the link by clicking **Share form** at the top of the **Registration** sidebar item. Send it to your participants — email, WhatsApp, parish bulletin, however you reach them.

---

## Step 6 — Watch registrations come in

The **People** tab shows everyone who's registered. Each person has a status:

- **pending** — registered but hasn't confirmed via the email link yet.
- **confirmed** — clicked the email link (or you confirmed them by hand).
- **cancelled** — they cancelled (or you cancelled on their behalf), whether before or after confirming.

Only **confirmed** participants enter the allocation engine. As registrations arrive, you can:

- Click any cell in a participant's row (name, email, group code, gender, date of birth, phone, etc.) to edit it inline.
- Change a participant's status inline via the dropdown on their row — useful when an email never arrived (school filter ate it; old address) and you need to confirm them by hand.
- Click **Notes** on a row to attach a note to a participant.
- Click **↓ Export data** in the Actions column to download all data Moimio holds on that participant (the GDPR export).
- Add **marks** — colour-coded badges like "Leader" or "Needs ground floor" — by clicking the small mark dot/+ icon next to a participant's name (in the People table, the AllocationBoard, or the Check-in panel).

---

## Step 7 — Run the allocation engine

When you're ready to allocate (typically after registration closes, but you can also run it earlier as a draft), go to **Organise**.

The Organise page shows your allocation categories side by side. Click a category and then **Auto-Allocate**. Before it runs, you'll be asked which mode to use:

- **Allocate new participants only** (top-up) — keeps existing assignments untouched and only places people who aren't yet allocated. Use this when you've already manually placed some specific people and want the engine to fill in the rest around them.
- **Reallocate everyone from scratch** — clears all current assignments in this category and runs a full reallocation. Use this when you've changed engine settings or marks and want a fresh proposal.

In either mode the engine:

1. Looks at all confirmed participants.
2. Tries to keep group-code clusters together.
3. Tries to honour mark behaviours (keep-together / spread-evenly).
4. Respects gender restrictions and capacity (these are hard — never violated).
5. Fills the remaining people round-robin across units.

The result is a **proposed allocation** — none of it is committed yet. You see who's in which unit and a list of anyone the engine couldn't place.

If the proposal looks wrong, you have options:

- **Tweak settings** (mark priorities, gender restriction, exclusive-group-codes toggle) and **Auto-Allocate** again with the **Reallocate from scratch** mode.
- **Drag specific people manually** to where you want them, then **Auto-Allocate** with **Allocate new participants only** — the engine fills around your manual placements without disturbing them. The most surgical option when you mostly like the proposal but want a few specific exceptions.
- **Manual override only.** Drag participants between units in the AllocationBoard and skip re-running. The engine doesn't lock you out; it proposes, you decide.

When you're happy, click **Commit allocation** at the top of the category. Now the assignments are committed.

---

## Step 8 — Generate rosters

Go to **Reports**. For each allocation category, you'll see download buttons:

- **Compact** — one row per unit, list of names. Good for noticeboards.
- **Sign-in** — printable check-in sheet with empty signature columns.

Click to download. The PDF language dropdown at the top lets you pick the language used in all rosters on the page (separate from your interface language). For raw participant data as CSV, use the **↓ Export ▾** dropdown at the top of the **People** page.

---

## Step 9 — Check people in on the day

Once the event has started (start_date arrived), the Event phase is in its **Live** sub-state. Open **Organise** and click **Enter check-in mode →** at the top right (admins only). Staff users with check-in permission see **Check-in** as its own sidebar item.

Either path opens the same panel. Click **+ Create column** to set up the tick-off columns you want (Welcome pack, Payment, etc.) — you can do this on the day or in advance via the same panel during Registration phase if you have pre-event check-in access. Tick people off as they show up. Each tick is per-participant, per-field — nothing fancy.

The check-in page works well on a tablet or phone. Several staff can check people in at the same time, on different devices — updates sync live across them.

---

## Step 10 — After the event

Once the end date passes, the event is in **Event phase, sub-state Done**. You can:

- Close the event manually if you haven't already (status → `closed`) — done from the **Registration overview page** during Registration phase, or via the **Registration is still open** banner that appears at the top of Organise during Event phase if registration was left open.
- Archive it for long-term storage (Super Admin only): **More ▸ Event details ▸ Danger zone ▸ Archive this event**, or via the **⋯** menu on the events list. Reversible.
- Duplicate it as a template for the next event — from the events list, click the **⋯** menu on the row, then **Duplicate**. Saves having to recreate categories, custom fields, and marks from scratch.

---

That's the full flow. Each numbered section in this manual covers one of the steps above in more depth — including edge cases, gotchas, and the underlying model.
