# 03 — People

The People table is where you'll spend most of your time during Registration phase. It's a list of everyone signed up for your event, with tools to view, edit, confirm, mark, and group them.


<p align="center">
  <img src="../assets/people-table.png" alt="People table with search box, status filter pills, Columns, Export and Import CSV buttons, and per-row actions" width="560">
  <br>
  <em>People table with search box, status filter pills, Columns, Export and Import CSV buttons, and per-row actions</em>
</p>


---

## The People table

Open **People** from the sidebar. You see a table with one row per registration. The columns shown by default are:

- **No.** — the participant's per-event sequential number (e.g. `#1`, `#12`). A lightweight, human-friendly ID. Always shown, always first.
- **Name** — full name as registered, followed by the participant's mark dots (see [Marks](04-marks.md)). Always shown.
- **Email**.
- **Group code** — the code they registered with, or the one Moimio generated for them. Hover over it (or long-press on a phone) to see who else shares that code.
- **Status** — Pending / Confirmed / Cancelled (colour-coded).
- **Registered** — date and time of the registration.
- **Notes** — opens the notes for that participant; a small number shows how many notes there are.
- **Actions** — per-row controls: **✉ Resend** (resend the registration email; hidden for cancelled participants), **↓ Export data** (the participant's full GDPR data export as JSON) and **Remove** (soft-delete the participant; event admins only).

Click **Columns** to show or hide more columns: **Gender**, **Date of Birth**, **Phone**, **Address**, **Country**, **Church / Organisation** and **Message** (these appear in the list once at least one participant has filled them in), **Checked In**, and every custom field from your registration form (under **Custom Fields**). You can also drag a column header (by its ⠿ handle) to change the column order.

The table supports:

- **Filtering by status.** Pills at the top: **All**, **Pending**, **Confirmed**, **Cancelled**. Under **All**, cancelled people sink to the bottom of the list and their names are struck through.
- **Sorting** — click any column header; click again to reverse.
- **Search** — matches name, email, group code, phone, church/organisation, and mark names. It's forgiving about accents, hyphens, apostrophes and umlaut spellings (searching "Mueller" finds "Müller").

Above the table, a counter shows how many participants match your search and filter (e.g. "12 of 80 participants").

Moimio remembers your column choices, column order and sort per user, in this browser, so the table looks the same next time you open it. (Sorting by a custom field works, but isn't remembered.)

There's no bulk-row-selection in the People table; per-row actions (edit, mark, export, remove) are one at a time.

### Mobile vs widescreen layout

On a phone or narrow tablet, each participant is shown as a card with number, name, marks, status, email and group code. Tap **▸ N details** (or **▸ More**) to expand the card and see the other columns you've switched on, plus **Resend**, **Export data** and **Remove**. On wider screens you get the full table with all columns side by side. The functionality is the same — only the layout differs.

---

## Editing fields directly in the table

You need permission to edit people (event admins, or staff with write access to People). Hover a value — an underline means you can click it.

**Name and email** — click the value. Moimio first asks you to confirm (**Edit name?** / **Edit email address?**), because you are changing personal data. Click **Edit**, change the value, then press Enter or click ✓. No email is sent.

**Group code** — click the code (or **+ Add** if there's none), type, press Enter or click ✓. Saves immediately.

**Status** — click the status pill. Three pills appear (Pending / Confirmed / Cancelled); click the one you want. ✕ closes without changing anything. See [Registration statuses](#registration-statuses) below.

**Gender, date of birth, phone, address, country, church/organisation** — click the value, change it, press Enter (or click ✓). A **Confirm change** window shows the old value → new value. Click **Confirm change** to save; **Cancel** discards.

**Custom fields** work the same way (with the confirmation window). The input matches the field type: text box for text, number box for numbers, dropdown for choice fields, ✓ / ✕ dropdown for yes/no fields, date picker for dates.

**Message is read-only** — it's the participant's message to the organisers, not for organisers to overwrite. Click **View** to read it in full.

**No.**, **Registered** and **Checked In** are set by Moimio and can't be edited here.

---

## Registration statuses

Every participant has a status. The status drives almost everything downstream — cancelled people are left out of allocation, check-in and most counts.

| Status | Meaning | How a participant gets here |
|---|---|---|
| **Pending** | Registered but hasn't clicked the email confirmation link yet. | Only happens when **Require email confirmation for registration** is switched on (More ▸ Registration form). |
| **Confirmed** | Registration is complete. | Straight after registering when email confirmation is off (the default), after clicking the email link, after a CSV import, or when an admin sets it by hand. |
| **Cancelled** | The participant withdrew, or you cancelled on their behalf. | Set by an admin. Cancelling takes the person out of any groups they were placed in. |

By default the allocation engine places pending participants too (the **Include unconfirmed people** setting — see [section 6](06-allocation-engine.md)).

You can change status from the row when:

- An email never arrived (spam filter ate it; old address). Change status to **Confirmed** by hand.
- Someone calls to cancel. Change status to **Cancelled**.
- Someone double-registered. Cancel one of them.

You can switch back and forth between statuses freely.

---

## Group codes

Group codes link related registrations so the allocation engine treats them as a cluster.

### How participants set their group code

The registration form includes an optional **group code** field. The convention is `STEM-NNN` (e.g. `SMITH-742`). A family of four registering together would all enter `SMITH-742`. The engine will then try to keep them together when allocating rooms (or any other group type).

If a registrant doesn't enter one, Moimio derives a stem from their surname and appends a unique numeric suffix — normally three digits (e.g. `SMITH-742`), rolling to four or five only if that surname already has many clusters in the event — and includes the result in the registration email, so the registrant can share it with anyone else who'd like to be grouped with them.

If a registrant types only a stem (e.g. `SMITH` with no number), the same logic applies — a unique suffix is added before saving. This is collision-safe: two unrelated families both typing `SMITH` end up with different codes, so they don't accidentally cluster together. To deliberately join an existing cluster, the registrant types the full code (`SMITH-742`); that's saved as typed. Codes are stored in capitals.

### How admins manage group codes

From the People table, you can:

- **Set or change** a participant's group code by clicking the value (or **+ Add**). Useful when someone registered without one and you realise they're with a family. Type the other person's full code to put them in the same cluster.
- **Check who's in a cluster** by hovering over a code. The pop-up lists everyone else with the same code, or says nobody else has it.

### Why "cluster of one" doesn't count

If a participant has a group code that nobody else shares, they're a "cluster of one." The engine treats them like any other individual. The group code is preserved (you can see it in the UI and reports), it just doesn't trigger any clustering behaviour.

---

## Notes

Click **Notes** on a row to open that participant's notes. Type in **Write a note...** and click **Add Note**.

- A note is **Private** by default — only you can see it. Tick **Share with team** before adding it to make it a **Team** note that other staff on the event can see.
- Each note shows who wrote it and when. If the author's account has since been deleted, it shows **[removed user]**.
- You can delete notes with the trash icon. Only the author (or a Super Admin) can actually delete a note.

The same notes appear in the participant's profile panel on the Organise board and in Check-in.

### History

A participant's allocation history — who placed them where, moves, removals, exclusions, and whether a person or the engine did it — isn't in the People table. Open their profile (**View profile**, the ⓘ icon) on the Organise board or in Check-in to see it. See [section 6](06-allocation-engine.md).

---

## Batch registration (CSV import)

For events where participants aren't using the public form — say, a closed retreat where attendees are pre-selected and you have a roster spreadsheet — you can import them directly.

From the top of the People table, click **↑ Import CSV**. The **Import participants** window opens:

1. Click **Download template** to get a CSV with the right column headers (including your custom fields).
2. Fill in your data and save it as CSV.
3. Under **Date format in your file**, pick **European (DD.MM.YYYY)** or **ISO / Korean (YYYY.MM.DD)** so dates of birth are read correctly.
4. Drop the file into the window (or click to choose it). Moimio shows a preview: 🟢 rows are fine, 🟡 rows have a warning, 🔴 rows have an error (missing first name, last name or email, invalid email, duplicate email within the file, invalid gender, unclear date, a value that isn't one of a choice field's options, and so on).
5. Click **Import N valid rows**. Rows with errors are skipped; rows with only warnings are imported.

Imported participants land in **Confirmed** status and get a participant number and (if needed) a generated group code. No emails are sent — the admin running the import is vouching for the addresses.

Watch the yellow warnings:

- **Already registered** — that email address is already in the event. The row is still imported, so you'd end up with two records for the same person. Remove the row from your file if that's not what you want.
- **No GDPR consent** — the row has no `true`/`yes` in the consent column.
- If every row has the same gender, Moimio warns you — spreadsheet programs sometimes auto-fill a value down a whole column.

The CSV format is forgiving:

- Column order doesn't matter, and common header spellings are recognised ("First Name", "Surname", "E-mail", "DOB", "Mobile", "Church" and so on).
- The People export columns `No.`, `Status`, `Checked In`, `Registered`, `Marks` and `Message` are silently ignored, so you can re-import an export.
- Other unrecognised columns are listed in a yellow banner in the preview. When you import, each one becomes a new custom field (hidden from the public registration form), and its column is switched on in the People table straight away. Note that the export's **Excluded From** column is treated this way too — delete that column before re-importing an export.
- Missing optional columns default to empty.
- **Mark assignments and exclusions are not imported.** Assign marks after import in the People table or on the Organise board.

For very large imports (>1,000 rows), break the file into batches of a few hundred to keep the preview snappy.

---

## Exporting

Two CSV export options at the top of the People table, under the **↓ Export ▾** button:

- **Full participant list** — every participant in the event (except removed ones), regardless of the search or status filter currently on screen. Columns: First Name, Last Name, Email, Gender, Date of Birth, Phone, Address, Country, Church/Organisation, Group Code, GDPR Consent, No., Status, Checked In, **Marks** (comma-separated mark names), **Excluded From** (the group types the person is excluded from), one column per custom field, and Message. Allocations are deliberately *not* in this CSV — for an allocation snapshot, use the roster PDFs in Reports or the backup.
- **Names + emails only** — a two-column CSV (Name, Email) suitable for pasting into a mailing-list tool.

There's also a per-row **↓ Export data** action (in the Actions column) that downloads the **GDPR data export** for one participant as JSON — see [section 9](09-data-export-gdpr.md).

---

## Common workflows

### "Their email never arrived"

In the People table, click the participant's **Pending** status pill and choose **Confirmed**. Done.

If you want them to get the email anyway, click **✉ Resend** on their row. A pending participant gets the confirmation link again; a confirmed participant gets the registration email with their group code.

### "Two people registered as the same person"

In the People table, find both rows (search by name or email). Pick the one to keep (usually the one confirmed first, or with more complete information). Set the other one to **Cancelled**. If the cancelled one had already been placed in groups, those places are freed automatically.

### "I want to mark all the leaders"

Create a mark under **More ▸ Marks** in the sidebar (or the **Marks** card in the Setup hub). Name it e.g. "Leader", pick a distinct colour, and make sure **People table** is ticked under **Visible in**.
Then in the People table, find each leader. Next to their name is a small ● button (a circle when they have no marks yet). Click it and click **Assign** next to "Leader".

### "Export everyone for a mailing list"

Use **↓ Export ▾ → Names + emails only**. Two-column CSV, paste straight into your mailing tool.

---

## When the participant later cancels

Two options:

- **Cancel** (status → **Cancelled**): the record stays visible in the People table (struck through, at the bottom of **All**, or under the **Cancelled** pill) but is left out of allocation, check-in and most counts. Any group places are freed. You can set them back to Pending or Confirmed at any time — useful for waiting-list recovery.
- **Remove** (the **Remove** action in the row's Actions column, event admins only): after you confirm **Remove Participant**, the person disappears from all lists, allocations and counts. The record is kept in the database for record-keeping (the GDPR data export still includes it — see [section 9](09-data-export-gdpr.md)), but there is no button to bring it back; restoring it needs someone with database access.

Full physical deletion of the record (for the rare case where regulatory context demands it) is also currently a manual database operation — see [section 9](09-data-export-gdpr.md) for the rationale.

---

## What's next

[Section 04 — Marks](04-marks.md) covers the mark system: defining colour-coded badges, attaching them to participants, and configuring how they influence the allocation engine.
