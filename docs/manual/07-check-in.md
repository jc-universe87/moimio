# 07 — Check-in

The check-in panel is what staff use on the day of the event to mark people as arrived. It's intentionally separate from the rest of the admin UI: a focused full-page view with big tick boxes, optimised for tablets at a registration desk.

<!-- TODO: screenshot at docs/assets/check-in.png — Check-in panel in immersive mode with tick boxes -->

---

## When check-in becomes available

In the **Event** phase (sub-states **Live** and **Preparing**) the **Check-in** item appears in the sidebar for everyone with check-in access — that's where you'll spend most of your time during the event.

In the **Registration** phase (before the event starts), Check-in is **not** in the sidebar — the focus during registration is on getting people signed up, not on ticking them in. But you can still reach the panel ahead of time to **configure your check-in columns** so you're ready on the day. Two paths:

- **Admins** (Super Admin or the event's admins) — open the **Registration overview** page (the default landing in Registration phase) and click the small **→ Set up the check-in panel** link below the Close registration / Share form buttons.
- **Staff with check-in write access AND the "Access before the event starts" sub-permission** — same link appears for them too. The sub-permission is set by an event admin in the Staff card (covered in section 11). Without it, staff get check-in only once the event starts.

In the **Setup** phase (event is `draft`, no registrations yet), Check-in isn't reachable for anyone. Configure things in the order: Setup hub → open registration → Registration phase → set up check-in columns → close registration → Event phase begins.

---

## Two views: panel vs immersive mode

There are two ways to use Check-in:

- **Inline panel** (`Check-in` in the sidebar) — embedded in the normal admin layout. Useful when you want to glance at check-in stats while doing other admin work, or for adjustments mid-event.
- **Immersive mode** (`Enter check-in mode →` button on the Organise page during the Event phase) — full-page overlay with no sidebar. The route is `/admin/events/{eventId}/checkin`. This is the view to use at the registration desk on a tablet.

The data is the same in both views — ticks made in either show up immediately in the other (and on every other connected device, see [Real-time sync](#real-time-sync) below).

---

## The check-in table

Each row is one confirmed participant. The default columns are:

- **No.** — the participant's per-event sequential number (e.g. `#001`).
- **Name**.
- **Group code** — visible since families/groups often arrive together.
- **Phone**.
- **Check-in** — a single tick column for "they've arrived".

There's also an optional **Check-in time** column, off by default. Toggle it on via **Columns** at the top of the table — once a participant is ticked in, this column shows the timestamp.

Above the rows: a **search box** (matches name, email, group code, phone), filter pills (All / Checked in / Not checked in), and a **+ Create column** button (admins only).

---

## Custom check-in columns

Beyond the built-in "Check-in" tick, you can add tick-off columns for anything you want to track at the door — payments collected, T-shirts handed out, name badges issued, signed liability waivers, etc.

To add a column, click **+ Create column** in the panel header. Type a name like "T-shirt", "Payment", "Welcome pack" — confirm. The column appears with empty tick boxes for every participant.

Custom columns can be deleted via the column header dropdown (admin only). Deletion removes the column and all its tick data — there's a confirmation dialog and the action is irreversible.

Use cases worth noting:

- **Multiple staff at the same desk** can independently tick different columns for the same participant (one ticks "Payment", the other ticks "T-shirt"). The data syncs.
- **Ticking the main "Check-in" column** is what counts toward the "X of Y checked in" stat. Custom columns are tracked separately and don't affect that count.

---

## What ticks mean and how they propagate

When a tick lands, three things happen:

1. **The DB row updates.** The tick is persistent — no separate save step.
2. **The check-in time records.** For the main check-in column only, the timestamp captures when the tick was placed.
3. **Other connected devices update within ~1–2 seconds** without a refresh — see below.

Multiple devices can check people in simultaneously — Postgres handles concurrent writes correctly. If two staff members tick the same person at the same moment, the result is just "ticked"; nobody sees an error. **Updates also propagate live across devices** — when one staff member ticks someone in, the change appears within a second or two on every other open Check-in screen for the same event, with no refresh needed.

---

## Real-time sync

Both views (inline and immersive) subscribe to a server-sent event stream for the event's check-in topic. When any tick happens — on any device — every connected client receives the change and updates its display within ~1–2 seconds.

The stream covers:

- The main **Check-in** tick + timestamp.
- All **custom column** ticks.

What you'll see in practice: a participant arrives at the door, staff member A ticks them in on her phone, staff member B watching the immersive screen at a different desk sees the row update instantly. No refresh button anywhere.

The connection is automatic — open the page, you're subscribed; close it, you're disconnected. There's no setup. If the network drops briefly the stream auto-reconnects when it returns.

---

## InsightPanel — full participant view

Each row's **(i)** icon (right side) opens the **InsightPanel** — a slide-in panel showing everything Moimio holds about that participant: contact details, registration history, current allocations across all categories, marks, notes. Useful when someone arrives and you need to verify who they are or what room they're in.

The InsightPanel is identical to the one in Organise — same data, same actions. Mark assignments made here (via the marks section) propagate live; same for notes.

---

## Common workflows

### "She's here but not on my list."

Search by name. If the row exists but says **Not checked in**, tick. If no row exists, the person never registered or is in `pending` status — open the People table (separate sidebar item), find them, change their status to `confirmed` inline. They appear in Check-in immediately. If they were on the registration list but you can't find them in check-in, check the People table — they might be in `pending` status (registered but not confirmed) or `cancelled`. Change their status inline in the People table to `confirmed`, then they appear in check-in.

### "I need to undo a tick."

Click the tick again. Toggles back to unticked. Check-in time clears.

### "Two staff are at the same desk — won't we collide?"

No. The system handles concurrent ticks correctly. The only thing to coordinate informally is who's typing in the search box at any given moment; both can tick freely.

### "We're using our own waiver/payment system at the door — can we just track the main tick?"

Yes. Don't create custom columns; the panel works fine with just the built-in Check-in.

### "How do I export today's arrivals?"

Reports section (next chapter) → CSV export from the People page filtered to "Checked in", or PDF roster including a check-in column.

---

## What's next

[Section 08 — Reports & PDF exports](08-reports-and-pdf-exports.md) covers the Reports tile, PDF roster downloads in different formats and languages, and how the per-category PDFs interact with the engine's allocation results.
