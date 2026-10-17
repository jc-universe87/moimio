# Moimio CE — GDPR Compliance

## Core Architectural Principle

**No centralised processing engine.** The entire Moimio stack runs within the deployment the organisation controls — local laptop, church server, or VPS. There is no Moimio central server that participant data is sent to.

## Data Flow

```
Participant → Registration Form → FastAPI → PostgreSQL
                                    ↑
                              (all local, no external calls)
```

Participant data stays inside your deployment. Only three things can
leave it, and each happens only if you set it up:

- **Email.** If you configure SMTP, confirmation emails (with the
  participant's first name, email address, event name and group code) are sent through the mail
  provider you chose. Without SMTP, no email is sent.
- **Outbound webhooks.** If you add a webhook endpoint, Moimio sends
  short notices to it (an event was created, deleted or allocated).
  These carry ids, timestamps and at most a rounded headcount, never
  participant data. The one exception is a workspace-deletion request,
  which carries the email address of the admin who asked. See
  [Outbound Webhooks](webhooks.md).
- **Files you download.** Exports and backups are files on your
  computer once downloaded; looking after them is up to you.

## Deployment Scenarios

| Scenario | Data Location | Security Responsibility |
|----------|--------------|------------------------|
| Self-hosted (local) | Organisation's hardware | Organisation |
| Self-hosted (VPS) | VPS provider's infrastructure | VPS provider (DPA required) |
| Managed hosting | The hosting provider's infrastructure | Hosting provider as your processor, under its own terms and DPA |

## Implemented today

- [x] GDPR consent checkbox on every public registration form; a registration without it is refused. (People added by CSV import are not asked: a row without a "true" consent value is imported with consent recorded as false and a warning. You need your own lawful basis for them.)
- [x] **A link to your own privacy notice** on the registration form (v1.0.6). A Super Admin sets the address under **Workspace** in the admin sidebar; the form then shows it right after the consent sentence. Leave it empty and nothing is shown. Moimio does not write the notice for you.
- [x] `deleted_at` soft delete on participant records
- [ ] Hard-purge UI for full physical erasure of participant records (still on the backlog; the soft-delete + manual SQL workflow covers the gap meanwhile)
- [x] **Minimal personal data in application logs, by default.** At the default `LOG_LEVEL=INFO`, logs do not contain participant names, addresses, dates of birth, or other rich personal data. Email addresses appear in a small number of operational log lines (failed-login attempts, email sent/skipped/failed) where they're load-bearing for diagnostics; these can be filtered or redacted by your log drain if your retention policy requires it. **Setting `LOG_LEVEL=DEBUG` changes this:** it turns on database query logging, which writes participant names, addresses and other details into the server log during ordinary use. Use it only briefly, for troubleshooting, and clear those logs afterwards. (Before v1.0.5 query logging was on by default.)
- [x] All data stored locally — no external API calls during registration other than the email and webhooks you configure
- [x] `.env` contains no participant data (it does hold passwords and secrets, so protect it)
- [x] **Admin-on-behalf data export** — JSON export of all data Moimio holds about a single participant, available from the participant's detail panel and the People table row actions. Event Admins and Super Admins only. See "Fulfilling Article 20 with Moimio" below.

## Planned

- [ ] Database-backed audit trail (who changed what, when, old/new values)
- [ ] Participant self-service data export (token-based; participant invokes their own DSAR without admin involvement)
- [ ] Encryption at rest via PostgreSQL pgcrypto
- [ ] Configurable data retention policies per event

## Public AI APIs (not implemented)

If AI features are introduced (e.g. a third-party AI API for allocation suggestions):

- Requires **explicit opt-in** per organisation
- **Separate consent mechanism** — distinct from registration consent
- Clear disclosure of what data is sent externally
- Architecture supports **local / bring-your-own-API-key** alongside any cloud option
- Organisations can choose to use no AI at all

## Sensitive Data Handling

### Never Logged (at the default log level)
- Passwords or password hashes
- Full JWT tokens
- Names, addresses, dates of birth, phone numbers, or other rich personal data beyond user IDs
- Credit card or payment data (future)

Email addresses appear in a small number of operational log lines (`login_failed`, `email_sent`, `email_skipped`, `email_failed`) where they're necessary for diagnostics. These are filterable by log-drain configuration if retention policies require redaction. With `LOG_LEVEL=DEBUG` the guarantees above no longer hold, because every database query is logged with its values.

### Stored Encrypted (planned, not implemented)
- Email addresses
- Phone numbers
- Addresses

### Soft delete (and manual erasure)
- **Soft delete:** Deleting a participant (Event Admin or Super Admin) sets a `deleted_at` timestamp. The person disappears from every screen, count, allocation run and new backup, but the row stays in the database and can be recovered. This is the default, one-click delete behaviour.
- **Deleting a whole event** physically removes everyone registered to it, including soft-deleted people, together with their answers, marks, placements, notes and history.
- **Manual erasure of one person:** physical removal of a single participant is a manual SQL operation by whoever runs the database — there's no screen for it yet. Marks, placements, exclusions and check-in ticks are removed with the row automatically. Custom-field answers, grouping preferences and notes are **not**: they must be deleted first (notes are linked by type `participant` and the participant's id). History rows stay but lose the link to the person and read as a removed participant. Preferences other people made naming this person by name or number are separate records and need checking by hand.
- **Copies elsewhere:** erasing the row does not reach backups or exports already downloaded, or whole-workspace export files. Delete or age out those copies under your own retention policy.

## Rights of Data Subjects

| Right | Implementation |
|-------|---------------|
| Right to access (Art. 15) | Admin-on-behalf data export. Participant self-service planned. |
| Right to rectification (Art. 16) | Edit the participant in the People table |
| Right to erasure (Art. 17) | Soft delete (one-click). Full physical erasure currently as manual SQL (see above); first-class UI still on the backlog. |
| Right to data portability (Art. 20) | Admin-on-behalf JSON export. Participant self-service planned. |
| Right to restrict processing (Art. 18) | Cancelled status approximates this — see manual §09. |

## Fulfilling Article 20 with Moimio

GDPR Article 20 obliges the data controller to provide a data subject's personal data in a "structured, commonly used and machine-readable format." For self-hosted Moimio deployments, the data controller is the deploying organisation — not Moimio.

### Workflow

1. Participant requests their data (typically by email to the organiser).
2. Admin opens the participant's detail panel (InsightPanel) from the allocation board, OR finds the participant row in the People table, and clicks **Export data**.
3. Browser downloads a single JSON file: `participant-export-{participant_number}-{date}.json` (the start of the participant's internal id stands in if they have no number).
4. Admin forwards the JSON file to the participant via whatever channel was used to receive the request.

### What the export contains

A single self-contained JSON document covering every Moimio table that touches this participant:

- **Export metadata** — schema version, when it was made, and a short note explaining what is left out.
- **Event metadata** — id, name, dates, location, description, timezone (so the export is interpretable on its own).
- **Participant base record** — name, email, gender, date of birth, phone, address, country, church/organisation, message, group code, registration status, consent, check-in status, language preference, timestamps. `deleted_at` is included when the participant has been soft-deleted (this is the moment they asked to be removed, which is legitimately their data). The email confirmation token is left out.
- **Custom field values** — each with its question label and type.
- **Marks** — resolved to `{name, colour, assigned_at}`.
- **Preference requests** — both directions: requests this participant made AND requests others made naming this participant by their participant number.
- **Current allocations** — resolved to `{category_name, unit_name}` with dates.
- **Exclusions** (v1.0.5) — the group types an organiser has kept this person out of, with the date. Who decided is not included.
- **Allocation history** — coarsened audit trail of every move and exclusion made on this participant. The identity of the admin who made each move is deliberately NOT included; that's the controller's metadata, not the data subject's data.
- **Notes** — only published notes attached to this participant, without the author's name. Private notes (only visible to their author) are the controller's working notes, not the data subject's data. Notes on the event, a group type or a room are not included.
- **Check-in values** — resolved to `{field_name, checked, ...}`.

### Soft-deleted records are exportable

Unlike most participant queries elsewhere in the codebase (which filter `deleted_at IS NULL`), the export endpoint deliberately includes soft-deleted participants. The DSAR use case explicitly covers the post-soft-delete window — a participant invoking right-to-access *after* having asked to be removed is exactly the case where the export must still work. Hard-purged records are unreachable by definition.

In practice: a soft-deleted person no longer appears in the People table or the allocation board, so the **Export data** button cannot be reached for them. The export itself still works through the API (`GET /api/events/{event_id}/participants/{participant_id}/data-export`, with the participant's id). If you expect a request, export first, then delete.

### Limits of the current implementation

- **Admin-on-behalf only.** There is no participant self-service flow. A participant cannot trigger their own export without going through the organiser. Self-service is on the post-v1.0 backlog.
- **No DSAR-of-DSAR audit row.** The export action itself is logged at the application level (`data_export_generated`, with ids only) and at the reverse-proxy access log, but no row is added to the audit trail recording "DSAR exported on {date} for {participant}." Operational logs cover this for now.
- **No automated email delivery.** The admin must forward the file manually.

## Other exports and backups

These hold personal data too; treat the files accordingly.

- **People spreadsheet (CSV)** from the People page — anyone with people-read access. Includes contact details, consent, custom-field answers, marks and, since v1.0.5, a column listing the group types each person is excluded from. An "emails only" variant holds just name and email. Soft-deleted people are left out.
- **Event backup** (Backup page) — Event Admins. A *full* backup holds the event's participants and everything about them: answers, marks, placements, exclusions, preferences, check-in ticks, notes and history. Soft-deleted people are left out. It carries published notes plus the downloader's own private notes, never another admin's private notes. Team members and their roles are never in a backup. A *structure-only* backup holds the event's set-up (group types, rooms, marks, form, check-in columns) and no personal data, not even the organiser's sender name and reply-to address, so it is safe to share as a template.
- **Whole-workspace export** (command line, see [Moving a workspace](moving-a-workspace.md)) — every event's full backup including every private note, plus a list of team accounts (names, emails, roles; no passwords) and webhook addresses (no secrets).

## Self-Hosting as Primary GDPR Solution

When an organisation self-hosts Moimio, they are the data controller and processor. No third party (including Moimio) has access to participant data. This is the strongest possible GDPR posture.
