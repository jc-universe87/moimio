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
| 01 | [Getting Started](01-getting-started.md) | The admin interface, the three event phases, your first session. |
| 02 | [Events and Registration](02-events-and-registration.md) | Creating events. Configuring the registration form. Custom fields. Opening for registration. Confirmation emails. |
| 03 | [People](03-people.md) | The People table. Status (pending / confirmed / cancelled). Editing, confirming, deleting participants. Group codes. Bulk import. |
| 04 | [Marks](04-marks.md) | Colour-coded badges for staff-visible tagging. Mark editor. How marks influence allocation. Priority order. |
| 05 | [Group Types and Units](05-group-types-and-units.md) | Allocation categories (Rooms, Small Groups, plus any you add). Units inside them. Capacity, gender restriction, exclusive vs overlapping rules. |
| 06 | [Allocation Engine](06-allocation-engine.md) | The five passes. What it guarantees and what it tries to achieve. The imbalance-by-design principle. Re-running, overriding, manual placement. |
| 07 | [Check-in](07-check-in.md) | Custom check-in fields. The on-arrival workflow. Tablet / phone use. |
| 08 | [Reports and PDF Exports](08-reports-and-pdf-exports.md) | Compact roster, detailed roster, sign-in sheet. CSV exports. What's printable. |
| 09 | [Data Export and GDPR](09-data-export-gdpr.md) | Per-participant Article 20 export. Soft delete and full erasure rationale. Backup and restore. |
| 10 | [Multi-event and Archive](10-multi-event-and-archive.md) | Running several events in parallel. Closing and archiving. Re-using a past event as a template. |
| 11 | [Staff and Permissions](11-staff-permissions.md) | Global roles (Super Admin, Staff). Per-event role (Event Admin, Staff). Per-event assignments. The five permission surfaces. |

---

## Conventions used throughout

- **Bold** text refers to a UI element you can click — a button, a tab, a menu item.
- `Monospace` text refers to a value, a setting key, or a technical concept.
- ▸ markers indicate a sequence of clicks, e.g. **Setup ▸ Group types ▸ + Add New Group Type**.
- Screenshots are included where they help orient you to the UI; some sections lean more on prose where the layout is straightforward or evolves quickly. Screenshots may drift slightly from the current build over time.

---

## When the manual doesn't have your answer

Three places to look:

- **[FAQ](../faq.md)** — common questions about scope, hosting, scaling, GDPR.
- **[Glossary](../glossary.md)** — definitions of Moimio-specific terms (cluster, mark, group code, etc.).
- **The auto-generated API documentation** at `http://localhost:6121/docs` (or wherever your backend lives) — for developers building against the API.

If none of those help, [open an issue](https://github.com/jc-universe87/moimio/issues/new?template=feature_request.md) — "the manual didn't cover X" is a perfectly valid feature request and the kind of feedback that makes the docs better.
