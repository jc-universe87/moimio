# 07 — Check-in

The check-in screen is what staff use on the day of the event to mark people as arrived. It's a simple list with big tick boxes, designed to work well on a tablet or phone at the registration desk.

<p align="center">
  <img src="../assets/check-in.png" alt="Check-in mode with the search box, progress bar and tick boxes" width="560">
  <br>
  <em>Check-in mode</em>
</p>

---

## Getting to check-in

What you see depends on who you are.

**Admins** (Super Admin or event admin) click **Enter check-in mode →** on the event's main page. The button appears during the Event phase, while the event is **Preparing** or **Live** (not once it's **Done**). It opens a full-screen view with no sidebar, showing only the event name, a theme switch and **Sign out**. **← Back to Organise** returns to the normal admin view. When every group type has been confirmed, the allocation board also offers a **Check-in is ready →** shortcut.

**Staff whose only permission is check-in** are taken straight to this full-screen view when they open the event during the Event phase. There's no exit button: this is their screen for the shift.

**Staff with check-in plus other permissions** (for example check-in and People) see **Check-in** in the sidebar. It opens the same check-in list inside the normal admin layout, so they can switch between duties.

Staff who have **Access before the event starts** can also open check-in during the Registration phase (see [Section 11](11-staff-permissions.md)).

Whichever way you get there, the data is the same: a tick on one device appears on every other screen within a second or two.

---

## The check-in list

Each row is one participant. Everyone who is registered appears, confirmed or still pending; cancelled registrations don't.

At the top:

- A **search box** (*"Search name, email, group code..."*). It also finds participant numbers and mark names, and it ignores accents, hyphens and spelling variants such as Müller / Mueller.
- A progress bar with *"28 of 34 checked in"*.
- Filter pills: **All**, **Checked in**, **Not checked in**.
- **Columns**, to choose which columns are shown.
- **+ Create column** (admins only).

The columns shown by default are:

- **No.**: the participant's number for this event.
- **Name**, with the person's mark dots (click them to see what the marks mean, or to assign marks if you're allowed to).
- **Check-in**: the main tick box for "they've arrived".
- **Check-in time**: when they were ticked in.

Click **Columns** to show or hide more. The list is grouped into **Check-in tracking** (your custom tick columns), **Registration fields** (**Group code**, **Gender**, **Phone**, **Church / Organisation**, **Country**, **Address**, **Date of Birth**, **Message**, **Registered** and **Check-in time**), **Custom fields** from your registration form, and **Other** (**Notes**, which adds a button to read and write notes on that person). Drag a column heading sideways to reorder, and click a heading to sort by it. Your column choices are remembered on that device.

On a phone, each person is a card with the name and tick boxes; tap **N details** to see the other columns.

---

## Custom check-in columns

Besides the main **Check-in** tick, you can add tick columns for anything you want to track at the door: payment collected, T-shirt handed out, name badge issued, signed waiver, and so on.

To add one, click **+ Create column**, type a name such as "Payment" or "T-shirt" and click **Add**. The new column appears with an empty tick box for every participant.

To delete a custom column, click the small ✕ next to its name in the column heading (admins only). A confirmation (**Delete Column**) warns you that the column and all its ticks are removed for everyone. This can't be undone.

Worth knowing:

- **Several staff can work on the same person at once**, for example one ticks "Payment" while another ticks "T-shirt".
- **Only the main Check-in tick counts as arrived.** Custom columns are tracked separately and don't change the "checked in" numbers.

---

## What a tick does

Ticks save immediately; there's no save button. Ticking the main **Check-in** box also records the time, shown in the **Check-in time** column. Click the tick again to undo it; the time is cleared too.

---

## Real-time sync

Every check-in screen stays connected to the server. When anyone ticks a box (main or custom, on any device), every other open screen updates within a second or two. There's no refresh button.

In practice: a participant arrives, staff member A ticks them in on her phone, and staff member B at the other end of the desk sees the row change straight away. Two people ticking the same person at the same moment is fine; the result is simply "ticked".

The connection is automatic. If the Wi-Fi drops briefly, the screen reconnects by itself when it comes back.

---

## Participant profile

Click the **ⓘ** next to a name (**View profile**) to open the **Participant profile**: contact details, registration details, which groups the person is in for every group type (handy for "which room am I in?"), their group preferences, custom fields and notes. It's the same panel as on the allocation board. To add a note or change marks, use the **Notes** column and the mark dots in the row.

---

## Common workflows

### "She's here but I can't find her."

Search for part of her name, her email or her group code. If you find her, tick her in. If she isn't in the list at all, her registration may have been cancelled, or she never registered. Ask an admin to check the **People** page: a cancelled registration can be set back to confirmed, and she then appears in check-in straight away.

### "I need to undo a tick."

Click the tick again. It goes back to unticked and the check-in time is cleared.

### "Two of us are at the same desk. Won't we get in each other's way?"

No. Each of you can search and tick on your own device, and both screens stay in step.

### "We use our own payment or waiver system. Can we just track arrivals?"

Yes. Don't create any custom columns; the main **Check-in** tick works on its own.

### "How do I get a list of who arrived?"

Two options:

- On **People**, click **↓ Export ▾ ▸ Full participant list**. The CSV has a **Checked In** column (Yes / No) for everyone.
- On **Reports**, the **Check-in** tile shows the running total during the Event phase. For a paper backup at the door, print the **Sign-in** roster (see [Section 08](08-reports-and-pdf-exports.md)).

---

## What's next

[Section 08 — Reports & PDF exports](08-reports-and-pdf-exports.md) covers the Reports page, printable roster PDFs in different formats and languages, and what the rosters show about your allocation.
