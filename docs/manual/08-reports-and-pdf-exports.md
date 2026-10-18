🌐 **English** · [Deutsch](08-reports-and-pdf-exports.de.md) · [한국어](08-reports-and-pdf-exports.ko.md) · [Español](08-reports-and-pdf-exports.es.md) · [Português (Brasil)](08-reports-and-pdf-exports.pt-BR.md) · [Français](08-reports-and-pdf-exports.fr.md)

# 08 — Reports & PDF exports

The **Reports** page gives you the headline numbers for your event at a glance and is where you download printable rosters: a few summary tiles at the top, and roster PDFs for each group type below.

<p align="center">
  <img src="../assets/reports.png" alt="Reports page with the summary tiles, PDF language selector and roster downloads" width="560">
  <br>
  <em>Reports page: summary tiles and roster downloads</em>
</p>

---

## Where to find Reports

**Reports** in the sidebar, during the Registration and Event phases. Admins and Super Admins always see it; staff see it if their permissions include reports.

The page has two parts:

- **Top: summary tiles**, for registration, allocation and (during the Event phase) check-in.
- **Bottom: Roster downloads**, one row per group type with **Compact** and **Sign-in** buttons.

---

## The summary tiles

### Registration

- **Headline:** the number of active registrations (confirmed plus pending; cancelled ones aren't counted).
- **Below it:** the breakdown, for example `26 confirmed · 5 pending · 2 cancelled`.

At a glance: are people signing up, and are the pending ones confirming?

### Allocation

- **Headline:** the share of active participants who are in at least one group, for example `87%`.
- **Below it:** `27 of 31 participants placed in groups`.

This counts people, not seats. 100% means every active participant is in at least one of your group types. Someone in both a room and a small group still counts once.

### Check-in *(Event phase only)*

- **Headline:** the share of active participants who have been ticked in, for example `82%`.
- **Below it:** `28 of 34 checked in`.

This tile only appears in the Event phase; before then there's nothing to check in.

---

## Roster downloads

Above the list of group types are two options that apply to every download on the page:

- **PDF language**: the language the PDF is printed in, whatever language you're using Moimio in. Choose from English, Deutsch, 한국어, Español, Português (BR) and Français. It starts out matching your interface language, so a German organiser can still print an English roster for an international team.
- **Include cover page**: adds a first page with the event name, dates, location and allocation numbers. Off by default to save paper; useful when handing a roster to a coordinator or keeping one for the records.

Each group type row shows its name and a summary such as `5 groups · 87% of participants`, with two buttons:

- **Compact**: names grouped by group, for clipboards and doors. Portrait A4.
- **Sign-in**: a sheet with a tick box, signature line and notes column for each person, for check-in staff. Landscape A4.

### The Detailed roster

A third format, the **Detailed** roster, lists full contact details (name, gender, date of birth, phone, email, group code). Because it contains personal data it isn't on the Reports page. Download it from the allocation board instead: **Organise ▸** open a group type **▸ ⋯ ▸ Detailed roster (PII)**, or **Detailed + cover page**. The **PDF** language picker just above those two entries sets the language. Admins can always download it; staff need permission to see People.

---

## What's in each PDF

Every page has a header with the event name, the group type and the format, plus a coloured strip so loose pages are easy to sort. The footer shows the event name and dates and *"Page 2 of 5"*.

### Compact

For each group:

- A header bar with the group's name, how many people are in it compared with its capacity (with a small fill bar), and its gender restriction if it has one.
- A bulleted list of members, sorted by surname. Each line shows the name, any mark dots, a gender initial and the group code.
- Groups with more than 6 people are printed in two columns to save paper.

### Sign-in

Landscape A4, with blank **DOOR STAFF** and **DATE** lines at the top. For each group, a header bar and then one row per person: a tick box, the name (with mark dots), group code, phone, a signature line and a notes space. Made to be printed, handed to someone with a clipboard and ticked by hand as people arrive.

### Detailed

Landscape A4. For each group, a header bar and a table with name (with mark dots), gender, date of birth, phone, email and group code. Use it when someone needs full contact details, for example a group leader or an external partner.

### The "Not allocated" page

If anyone in this group type isn't in a group, every format (Compact, Sign-in and Detailed) ends with a **NOT ALLOCATED** page listing them with their phone and email, in two blocks:

- **EXCLUDED**: people you deliberately kept out of this group type (see [Section 06](06-allocation-engine.md#keeping-someone-out-of-a-group-type)).
- **NOT PLACED**: people who simply haven't been put in a group yet.

A block is left out when it would be empty, and the page is left out entirely when everyone is placed. Cancelled registrations never appear.

### Cover page

When **Include cover page** is ticked, the PDF starts with a cover showing the event name, dates and location, the group type and format, three figures (**TOTAL**, **ALLOCATED** and **UNALLOCATED**, the last highlighted when it isn't zero), and when and by whom it was generated.

---

## Marks in PDFs

Marks that are visible in **Organise** appear as small coloured dots right after each person's name, in all three formats. A **Marks** legend at the end of the roster shows which colour means which mark, listing only marks that actually appear in that PDF.

If someone has more marks than fit (4 dots in Compact and Detailed, 3 on the Sign-in sheet), the extra ones are left off. Marks are shown in alphabetical order so every printout looks the same.

---

## A quick printable view

On the allocation board, **⋯ ▸ ↗ Open overview** opens a read-only view of the group type in a new tab, with a **🖨 Print** button. Handy for a quick printout of the current state without downloading a PDF.

---

## What about CSV?

Spreadsheet exports live on the **People** page, not Reports. Click **↓ Export ▾** and choose **Full participant list** (every field, including **Status**, **Checked In**, **Marks** and **Excluded From** columns) or **Names + emails only** (for a mailing-list tool). The People CSV doesn't list who is in which group; for that, use the roster PDFs or a backup.

---

## When the page is empty

If there are no registrations and no group types yet, the page just says *"Open registration to start collecting data. Reports populate from there."* If there are no group types, the roster section says *"No group types yet."* Everything fills in as registrations and allocations come in.

---

## What's next

[Section 09 — Data export & GDPR](09-data-export-gdpr.md) covers per-participant data exports (the Article 15 / Article 20 path), event-level backups, and how Moimio handles deletion and erasure.
