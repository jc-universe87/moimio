🌐 **English** · [Deutsch](README.de.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português (Brasil)](README.pt-BR.md) · [Français](README.fr.md)

# User Manual

This manual explains how to use Moimio to run an event end-to-end. It assumes you've already installed Moimio and logged in — if you haven't, start with the [Installation Guide](../installation/README.md).

> This manual covers **Moimio CE (Community Edition)**, the open-source self-hostable build. The same workflow applies to the managed hosted product at [moimio.app](https://moimio.app) — both editions share the same code.

---

## How to read this manual

You probably don't need to read it cover-to-cover. Two recommended paths:

### → If you want to run an event by tomorrow

Read the **[Quick Guide](quick-guide.md)** (~10 minutes). It walks through one full event from creation to PDF export, skipping detail and edge cases. You'll know enough to run something.

### → If you want to understand the whole product

Read the numbered sections in order. Each focuses on one feature area. About 30 minutes total.

---

## Sections

| # | Section | What's in it |
|---|---|---|
| | [Quick Guide](quick-guide.md) | One event, beginning to end, in ten minutes of reading. |
| 01 | [Getting Started](01-getting-started.md) | First-time setup and signing in. The admin layout, the three event phases (Setup, Registration, Event), user accounts, the events list, your first session. |
| 02 | [Events and Registration](02-events-and-registration.md) | Creating events. The Setup hub. Configuring the registration form, custom fields and group codes. Opening and closing registration. Confirmation emails. |
| 03 | [People](03-people.md) | The People table. Status (pending / confirmed / cancelled). Editing in the table, group codes, notes, CSV import, exports. |
| 04 | [Marks](04-marks.md) | Colour-coded badges for tagging participants. The mark editor. Mark priorities per group type. Reserving a group for a mark. |
| 05 | [Group Types and Units](05-group-types-and-units.md) | Group types (Room Allocation, Small Groups, plus any you add) and the groups inside them. Capacity, gender, mark restrictions. Keeping someone out of a group type. Exporting and importing a layout. |
| 06 | [Allocation Engine](06-allocation-engine.md) | What the engine does, in plain language. Engine settings. Reviewing a proposal, locking groups, re-running, manual adjustments, history and reasons. |
| 07 | [Check-in](07-check-in.md) | The check-in list. Custom check-in columns. Real-time sync across tablets and phones. |
| 08 | [Reports and PDF Exports](08-reports-and-pdf-exports.md) | Dashboard tiles. Compact, Sign-in and Detailed roster PDFs. Marks in PDFs. CSV exports. |
| 09 | [Data Export and GDPR](09-data-export-gdpr.md) | A participant's personal data export. Editing, removing and erasing. Privacy notice link. Full and structure-only backups, restoring, moving a workspace. |
| 10 | [Multi-event and Archive](10-multi-event-and-archive.md) | The events list. Archiving and unarchiving. Starting a new event from a past one's settings. Running several events in parallel. |
| 11 | [Staff and Permissions](11-staff-permissions.md) | User accounts (Super Admin, Staff) and deleting users. Each event's team: Event Admin or Staff. The five permission settings. |

---

## Conventions used throughout

- **Bold** text refers to a UI element you can click — a button, a tab, a menu item.
- `Monospace` text refers to a value, a setting key, or a technical concept.
- ▸ markers indicate a sequence of clicks, e.g. **Users ▸ + New User ▸ Create User**.
- Screenshots are included where they help orient you to the UI; some sections lean more on prose where the layout is straightforward or evolves quickly. Screenshots may drift slightly from the current build over time.

---

## When the manual doesn't have your answer

Three places to look:

- **[FAQ](../faq.md)** — common questions about scope, hosting, scaling, GDPR.
- **[Glossary](../glossary.md)** — definitions of Moimio-specific terms (cluster, mark, group code, etc.).
- **The auto-generated API documentation** at `http://localhost:6121/docs` (or wherever your backend lives) — for developers building against the API.

If none of those help, [open an issue](https://github.com/pistio/moimio/issues/new?template=feature_request.md) — "the manual didn't cover X" is a perfectly valid feature request and the kind of feedback that makes the docs better.
