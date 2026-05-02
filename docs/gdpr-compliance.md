# Moimio CE — GDPR Compliance

## Core Architectural Principle

**No centralised processing engine.** The entire Moimio stack runs within the deployment the organisation controls — local laptop, church server, or VPS. There is no Moimio central server that participant data is sent to.

## Data Flow

```
Participant → Registration Form → FastAPI → PostgreSQL
                                    ↑
                              (all local, no external calls)
```

No data leaves the deployment boundary in Phase 1.

## Deployment Scenarios

| Scenario | Data Location | Security Responsibility |
|----------|--------------|------------------------|
| Self-hosted (local) | Organisation's hardware | Organisation |
| Self-hosted (VPS) | VPS provider's infrastructure | VPS provider (DPA required) |
| Managed hosting (future) | Vetted European VPS | Moimio + VPS provider (DPA in place) |

## Phase 1 — Implemented

- [x] GDPR consent checkbox on every registration form
- [x] `deleted_at` soft delete on participant records
- [ ] Hard-purge UI for full physical erasure of participant records (post-1.0 backlog; the soft-delete + manual SQL workflow covers the gap meanwhile)
- [x] **Minimal PII in application logs.** Application logs do not contain participant names, addresses, dates of birth, or other rich PII. Email addresses appear in a small number of operational log lines (failed-login attempts, SMTP send/skip events) where they're load-bearing for diagnostics; these can be filtered or redacted by your log drain if your retention policy requires it.
- [x] All data stored locally — no external API calls during registration
- [x] `.env` contains no PII
- [x] **Admin-on-behalf data export** — JSON export of all data Moimio holds about a single participant, available from the InsightPanel and PeopleTable row actions. Admin-only. See "Fulfilling Article 20 with Moimio" below.

## Phase 2+ — Planned

- [ ] Database-backed audit trail (who changed what, when, old/new values)
- [ ] Participant self-service data export (token-based; participant invokes their own DSAR without admin involvement)
- [ ] Encryption at rest via PostgreSQL pgcrypto
- [ ] Configurable data retention policies per event

## Public AI APIs (Phase 3+)

If AI features are introduced (e.g. Claude or Gemini APIs for allocation suggestions):

- Requires **explicit opt-in** per organisation
- **Separate consent mechanism** — distinct from registration consent
- Clear disclosure of what data is sent externally
- Architecture supports **local / bring-your-own-API-key** alongside any cloud option
- Organisations can choose to use no AI at all

## Sensitive Data Handling

### Never Logged
- Passwords or password hashes
- Full JWT tokens
- Names, addresses, dates of birth, phone numbers, or other rich PII beyond user IDs
- Credit card or payment data (future)

Email addresses appear in a small number of operational log lines (e.g. `login_failed`, `email_sent`) where they're necessary for diagnostics. These are filterable by log-drain configuration if retention policies require redaction.

### Stored Encrypted (Phase 2+)
- Email addresses
- Phone numbers
- Addresses

### Soft delete (and manual erasure)
- **Soft delete:** Sets `deleted_at` timestamp. Record excluded from queries but recoverable. This is the default, one-click delete behaviour.
- **Manual erasure:** Full physical removal of the participant row plus FK-cascading data (notes, assignments, custom field values, etc.). Currently a manual SQL operation against the soft-deleted record — there's no first-class UI in v1.0. Sufficient for the rare cases where the controller needs demonstrable physical removal.

## Rights of Data Subjects

| Right | Implementation |
|-------|---------------|
| Right to access (Art. 15) | Admin-on-behalf data export. Participant self-service planned. |
| Right to rectification (Art. 16) | Edit participant endpoint |
| Right to erasure (Art. 17) | Soft delete (one-click). Full physical erasure currently as manual SQL; first-class UI on post-1.0 backlog. |
| Right to data portability (Art. 20) | Admin-on-behalf JSON export. Participant self-service planned. |
| Right to restrict processing (Art. 18) | Cancelled status approximates this — see manual §09. |

## Fulfilling Article 20 with Moimio

GDPR Article 20 obliges the data controller to provide a data subject's personal data in a "structured, commonly used and machine-readable format." For self-hosted Moimio deployments, the data controller is the deploying organisation — not Moimio.

### Workflow

1. Participant requests their data (typically by email to the organiser).
2. Admin opens the participant's InsightPanel from the AllocationBoard, OR finds the participant row in the People table, and clicks **Export data**.
3. Browser downloads a single JSON file: `participant-export-{participant_number}-{date}.json`.
4. Admin forwards the JSON file to the participant via whatever channel was used to receive the request.

### What the export contains

A single self-contained JSON document covering every Moimio table that touches this participant:

- **Event metadata** — id, name, dates, location, description, timezone (so the export is interpretable on its own).
- **Participant base record** — name, email, contact details, group code, registration status, consent flags, language preference, timestamps. `deleted_at` is included when the participant has been soft-deleted (this is the moment they asked to be removed, which is legitimately their data).
- **Custom field values** — resolved against current field definitions for human-readable labels.
- **Marks** — resolved to `{name, colour, assigned_at}`.
- **Preference requests** — both directions: requests this participant made AND requests others made naming this participant by their participant number.
- **Current allocations** — resolved to `{unit_name, category_name}`.
- **Allocation history** — coarsened audit trail of every move made on this participant. The identity of the admin who made each move is deliberately NOT included; that's the controller's metadata, not the data subject's data.
- **Notes** — only published notes addressed to this participant. Internal admin draft notes (`is_published=False`) are the controller's working notes, not the data subject's data.
- **Check-in values** — resolved to `{field_name, checked, ...}`.

### Soft-deleted records are exportable

Unlike most participant queries elsewhere in the codebase (which filter `deleted_at IS NULL`), the export endpoint deliberately includes soft-deleted participants. The DSAR use case explicitly covers the post-soft-delete window — a participant invoking right-to-access *after* having asked to be removed is exactly the case where the export must still work. Hard-purged records are unreachable by definition.

### Limits of the current implementation

- **Admin-on-behalf only.** There is no participant self-service flow. A participant cannot trigger their own export without going through the organiser. Self-service is on the post-v1.0 backlog.
- **No DSAR-of-DSAR audit row.** The export action itself is logged at the application level (`data_export_generated`) and at the reverse-proxy access log, but no row is added to the audit trail recording "DSAR exported on {date} for {participant}." Operational logs cover this for v1.0.
- **No automated email delivery.** The admin must forward the file manually.

## Self-Hosting as Primary GDPR Solution

When an organisation self-hosts Moimio, they are the data controller and processor. No third party (including Moimio) has access to participant data. This is the strongest possible GDPR posture.
