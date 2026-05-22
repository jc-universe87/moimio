"""Batch registration service — CSV parsing, validation, template generation."""

import csv
import io
import re
import uuid
from datetime import datetime

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.custom_field import CustomFieldDefinition
from app.models.participant import Participant

# Fields that appear in every event's CSV template (fixed columns)
FIXED_COLUMNS = [
    "first_name",
    "last_name",
    "email",
    "gender",           # male | female | (blank)
    "date_of_birth",    # YYYY-MM-DD or blank
    "phone",
    "address",
    "country",
    "church_organisation",
    "group_code",
    "gdpr_consent",     # true | false
]


# v0.50f-4: lenient-import header aliases.
# Maps from normalised (lowercased, punctuation-stripped) versions of
# common user-visible headers — including the ones the export produces
# ("First Name", "GDPR Consent" etc.) — to the canonical snake_case keys
# used internally. A row read by csv.DictReader with "First Name" as a
# header becomes accessible via raw["first_name"] after normalisation.
FIXED_HEADER_ALIASES: dict[str, str] = {
    # First name variants
    "first name": "first_name",
    "firstname": "first_name",
    "given name": "first_name",
    "first_name": "first_name",
    # Last name
    "last name": "last_name",
    "lastname": "last_name",
    "surname": "last_name",
    "family name": "last_name",
    "last_name": "last_name",
    # Email
    "email": "email",
    "email address": "email",
    "e-mail": "email",
    # Gender
    "gender": "gender",
    "sex": "gender",
    # DOB
    "date of birth": "date_of_birth",
    "dob": "date_of_birth",
    "birth date": "date_of_birth",
    "date_of_birth": "date_of_birth",
    # Phone
    "phone": "phone",
    "phone number": "phone",
    "mobile": "phone",
    "tel": "phone",
    # Address
    "address": "address",
    # Country
    "country": "country",
    "nationality": "country",
    # Church / org
    "church": "church_organisation",
    "organisation": "church_organisation",
    "organization": "church_organisation",
    "church/organisation": "church_organisation",
    "church/organization": "church_organisation",
    "church organisation": "church_organisation",
    "church_organisation": "church_organisation",
    # Group code
    "group code": "group_code",
    "group": "group_code",
    "group_code": "group_code",
    # GDPR consent
    "gdpr consent": "gdpr_consent",
    "consent": "gdpr_consent",
    "gdpr": "gdpr_consent",
    "gdpr_consent": "gdpr_consent",
}


# v0.85 #16: headers we recognise as Moimio-export-only — always silently
# ignored on import. These appear when an admin downloads the People CSV
# and re-imports it (e.g. to bulk-edit). Without this allow-list, columns
# like "No." and "Status" would get promoted to custom fields on import.
# Stored already-normalised (lowercased, punctuation-stripped) so the
# match is straightforward.
IGNORED_HEADERS_NORMALISED: set[str] = {
    "no",
    "status",
    "marks",                # v0.83: marks column added to export
    "checked in",           # boolean column on export
    "registered",           # registration timestamp on export
    "message",              # message field — read-only, not editable via import
}


def _normalise_header(h: str) -> str:
    """Strip punctuation and lowercase a CSV column header for matching.

    Examples:
      'First Name'          → 'first name'
      'Church/Organisation' → 'church/organisation'  (/ preserved for alias match)
      '  GDPR Consent  '    → 'gdpr consent'
      'first_name'          → 'first_name'
    """
    return (h or "").strip().lower()


def _build_row_mapper(
    headers: list[str],
    custom_fields: list[CustomFieldDefinition],
) -> tuple[dict[str, str], list[str]]:
    """Build a map from the CSV's actual header strings to canonical keys,
    plus a list of unknown-column header strings.

    Canonical keys are either FIXED_COLUMNS entries (e.g. 'first_name') or
    'cf:<uuid>' for existing custom fields. Headers that don't match
    anything are returned as the second element of the tuple — the caller
    can decide whether to drop them, promote them to new custom fields,
    or surface them in the preview for the admin to choose.

    v0.85 #16: returns the unknown list (was: silently dropped) so the
    importer can offer to auto-create custom fields from new columns.
    Headers in IGNORED_HEADERS_NORMALISED are still silently dropped —
    they're Moimio-export-only and never represent participant data.

    Custom fields match by LABEL (case-insensitive) OR by their cf:<uuid>
    format, so exports with human labels round-trip correctly and so do
    internal cf:<uuid>-style CSVs.
    """
    mapping: dict[str, str] = {}
    unknown: list[str] = []
    # Label → cf:<uuid> lookup, case-insensitive
    cf_label_to_key = {
        _normalise_header(cf.label): f"cf:{cf.id}"
        for cf in custom_fields
    }
    # Also accept the internal cf:<uuid> form unchanged
    cf_uuid_keys = {f"cf:{cf.id}" for cf in custom_fields}

    for h in headers:
        if h is None or not h.strip():
            continue
        norm = _normalise_header(h)
        if norm in FIXED_HEADER_ALIASES:
            mapping[h] = FIXED_HEADER_ALIASES[norm]
        elif norm in cf_label_to_key:
            mapping[h] = cf_label_to_key[norm]
        elif h in cf_uuid_keys:  # internal form, case-sensitive match
            mapping[h] = h
        elif norm in IGNORED_HEADERS_NORMALISED:
            # Moimio-export-only column; silently ignored.
            pass
        else:
            unknown.append(h)
    return mapping, unknown


def _remap_row(raw: dict, header_mapping: dict[str, str]) -> dict:
    """Apply the header mapping to a single DictReader row.

    Returns a new dict keyed by canonical keys. Unknown keys are dropped.
    If two source columns both map to the same canonical key (e.g. both
    "First Name" and "first_name" present), the later one wins — this is
    almost never going to happen in practice.
    """
    out: dict = {}
    for src_key, val in raw.items():
        dst_key = header_mapping.get(src_key)
        if dst_key:
            out[dst_key] = val
    return out


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_VALID_GENDERS = {"male", "female", ""}


# v1.0-pre #15: smart date-of-birth parser. Accepts a handful of
# common shapes that spreadsheet apps emit when a date column has been
# touched, returns ISO YYYY-MM-DD on success, "ambiguous" for rows
# the parser refuses to guess at (e.g. "1/5/2003" where the parser
# can't safely pick between US-MDY and EU-DMY), or None for genuinely
# unparseable input.
import re as _re

# East Asian date pattern: YYYY년 MM월 DD일 (Korean), YYYY年 M月 D日
# (Chinese / Japanese). Whitespace is optional.
_EA_DATE_RE = _re.compile(
    r"^\s*(\d{4})\s*[년年]\s*(\d{1,2})\s*[월月]\s*(\d{1,2})\s*[일日]?\s*$"
)
# All-digit separators: -, /, ., 년월일 with no leading text
_NUM_DATE_RE = _re.compile(r"^\s*(\d{1,4})[\-/.](\d{1,2})[\-/.](\d{1,4})\s*$")


def _to_iso_date(year: int, month: int, day: int) -> str | None:
    try:
        return datetime(year, month, day).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def _parse_dob_smart(raw: str, *, dob_format: str = "eu"):
    """Return ISO 'YYYY-MM-DD', the literal string 'ambiguous', or None.

    v1.0.0o: ``dob_format`` resolves ambiguous numeric dates where the
    first two components are both ≤ 12 (e.g. ``01.05.2000`` — could be
    1 May or 5 Jan). Values:
      - ``"eu"`` (default): treat as DD.MM.YYYY (or DD.MM.YY).
      - ``"iso"``: treat as YYYY.MM.DD (the year-first case covers
        both ISO and Korean conventions — same shape).
    Other values fall back to ``"eu"``. When ``dob_format`` doesn't
    apply (one of the first two is > 12, so the date is already
    unambiguous), the value is parsed deterministically regardless.
    """
    s = raw.strip()
    if not s:
        return None

    # 1) ISO direct (also handles YYYY/MM/DD, YYYY.MM.DD).
    iso_re = _re.match(r"^\s*(\d{4})[\-/.](\d{1,2})[\-/.](\d{1,2})\s*$", s)
    if iso_re:
        y, m, d = (int(iso_re.group(i)) for i in (1, 2, 3))
        return _to_iso_date(y, m, d)

    # 2) East Asian shape (year-month-day with character separators).
    ea = _EA_DATE_RE.match(s)
    if ea:
        y, m, d = (int(ea.group(i)) for i in (1, 2, 3))
        return _to_iso_date(y, m, d)

    # 3) Excel serial number. Dates as numbers in Excel start at 1900-01-01
    # (= 1) with the 1900 leap-year quirk. Heuristic: 4–6 digit pure number,
    # value > 365 (filters out "5" or "31" as accidental DOB), < 80,000
    # (~year 2118). Matches typical real DOB serials.
    num = _re.match(r"^\s*(\d{4,6})\s*$", s)
    if num:
        n = int(num.group(1))
        if 365 < n < 80000:
            try:
                # Excel uses 1899-12-30 as serial 0 (correcting for the
                # leap-year quirk). Matches what Excel emits when saving.
                from datetime import timedelta
                base = datetime(1899, 12, 30)
                d = base + timedelta(days=n)
                return d.strftime("%Y-%m-%d")
            except OverflowError:
                return None

    # 4) Numeric three-component date (no clear year position).
    nm = _NUM_DATE_RE.match(s)
    if nm:
        a, b, c = (int(nm.group(i)) for i in (1, 2, 3))
        # Position-of-year heuristic. If first or last component is 4-digit,
        # that's the year and the other two are month/day. If the year is
        # last (the spreadsheet-mangled case), we still need to disambiguate
        # MDY vs DMY for the first two.
        if len(nm.group(1)) == 4:
            # YYYY-?-?
            y, m_or_d1, m_or_d2 = a, b, c
            # If second > 12, it's day-month (uncommon ISO-ish) → swap.
            if m_or_d1 > 12 and m_or_d2 <= 12:
                return _to_iso_date(y, m_or_d2, m_or_d1)
            # Otherwise treat second as month, third as day (ISO-like).
            return _to_iso_date(y, m_or_d1, m_or_d2)
        if len(nm.group(3)) == 4:
            # ?-?-YYYY — the spreadsheet-mangled case. Disambiguate:
            y = c
            if a > 12 and b <= 12:
                # Definitely DMY (first > 12 can only be day).
                return _to_iso_date(y, b, a)
            if b > 12 and a <= 12:
                # Definitely MDY.
                return _to_iso_date(y, a, b)
            # Both ≤ 12 — genuinely ambiguous. v1.0.0o: resolve per hint.
            # "iso" cannot apply here (year is last, not first) so the
            # only meaningful hint is "eu" → DMY. Anything else (or
            # historical "auto") falls back to refusing the guess.
            if dob_format == "eu":
                return _to_iso_date(y, b, a)
            return "ambiguous"
        # Two-digit year fallback: assume 2-digit year is in the last
        # position (DD-MM-YY or MM-DD-YY). For DOB, year 70..99 → 19xx;
        # 0..69 → 20xx. Same disambiguation rule for first two.
        if len(nm.group(3)) == 2:
            yy = c
            year = 1900 + yy if yy >= 30 else 2000 + yy
            if a > 12 and b <= 12:
                return _to_iso_date(year, b, a)
            if b > 12 and a <= 12:
                return _to_iso_date(year, a, b)
            # v1.0.0o: same hint-driven resolution for short-year DMY.
            if dob_format == "eu":
                return _to_iso_date(year, b, a)
            return "ambiguous"
        return None

    return None


def _validate_row(
    row_num: int,
    raw: dict,
    custom_fields: list[CustomFieldDefinition],
    seen_emails: set[str],
    existing_emails: set[str],
    *,
    dob_format: str = "eu",  # v1.0.0o
) -> dict:
    """
    Validate a single CSV row.

    Returns:
        {
            row_num: int,
            data: dict,           # cleaned values ready for ParticipantRegister
            errors: [str],        # fatal — row will be skipped on commit
            warnings: [str],      # non-fatal — row will still be committed
            valid: bool,          # True iff errors is empty
        }
    """
    errors: list[str] = []
    warnings: list[str] = []
    data: dict = {}

    # ── Required fields ──────────────────────────────────────────────────────
    for field in ("first_name", "last_name", "email"):
        val = raw.get(field, "").strip()
        if not val:
            errors.append(f"missing_required:{field}")
        else:
            data[field] = val

    # ── Email format + duplicate checks ──────────────────────────────────────
    email = data.get("email", "")
    if email:
        if not _EMAIL_RE.match(email):
            errors.append("invalid_email")
        else:
            email_lower = email.lower()
            if email_lower in seen_emails:
                errors.append("duplicate_email_in_file")
            else:
                seen_emails.add(email_lower)
                if email_lower in existing_emails:
                    warnings.append("duplicate_email_existing")

    # ── Gender ───────────────────────────────────────────────────────────────
    gender_raw = raw.get("gender", "").strip().lower()
    if gender_raw not in _VALID_GENDERS:
        errors.append("invalid_gender")
    else:
        data["gender"] = gender_raw or None

    # ── date_of_birth ─────────────────────────────────────────────────────────
    # v1.0-pre #15: smart-parse common spreadsheet date formats so the
    # CSV template survives a round-trip through Excel/LibreOffice/Numbers
    # without forcing the organiser to fight cell formatting. Accepts:
    #   - ISO 8601: 2003-05-01, 2003/05/01, 2003.05.01
    #   - DMY: 01/05/2003, 1.5.2003, 01-05-2003
    #   - MDY: 05/01/2003, 5/1/2003 (only when distinguishable from DMY)
    #   - East Asian: 2003년 5월 1일, 2003년 05월 01일
    #   - Excel serial number: 37742 (days since 1899-12-30)
    # Ambiguous purely-numeric like "1/5/2003" where both components
    # are ≤ 12 are rejected with `ambiguous_date_of_birth` so the
    # importer can prompt the user to clarify (or re-export with ISO).
    dob_raw = raw.get("date_of_birth", "").strip()
    if dob_raw:
        parsed = _parse_dob_smart(dob_raw, dob_format=dob_format)
        if parsed == "ambiguous":
            errors.append("ambiguous_date_of_birth")
        elif parsed is None:
            errors.append("invalid_date_of_birth")
        else:
            data["date_of_birth"] = parsed
    else:
        data["date_of_birth"] = None

    # ── Optional fixed fields ─────────────────────────────────────────────────
    for field in ("phone", "address", "country", "church_organisation", "group_code"):
        data[field] = raw.get(field, "").strip() or None

    # ── gdpr_consent ─────────────────────────────────────────────────────────
    gdpr_raw = raw.get("gdpr_consent", "").strip().lower()
    if gdpr_raw in ("true", "1", "yes"):
        data["gdpr_consent"] = True
    else:
        # Treat missing/false as False — not an error, but warn
        data["gdpr_consent"] = False
        warnings.append("gdpr_consent_false")

    # ── Custom fields ─────────────────────────────────────────────────────────
    custom_data: dict[str, str] = {}
    for cf in custom_fields:
        col_key = f"cf:{cf.id}"  # CSV column header format: cf:<uuid>
        raw_val = raw.get(col_key, "").strip()

        if cf.is_required and not raw_val:
            errors.append(f"missing_required_custom:{cf.label}")
            continue

        if not raw_val:
            continue

        if cf.field_type == "number":
            try:
                float(raw_val)
            except ValueError:
                errors.append(f"invalid_number:{cf.label}")
                continue

        elif cf.field_type == "boolean":
            if raw_val.lower() not in ("true", "false", "1", "0", "yes", "no"):
                errors.append(f"invalid_boolean:{cf.label}")
                continue

        elif cf.field_type == "date":
            try:
                datetime.strptime(raw_val, "%Y-%m-%d")
            except ValueError:
                errors.append(f"invalid_date:{cf.label}")
                continue

        elif cf.field_type == "select":
            options = (cf.options or {}).get("choices", [])
            if options and raw_val not in options:
                errors.append(f"invalid_option:{cf.label}:{raw_val}")
                continue

        custom_data[str(cf.id)] = raw_val

    if custom_data:
        data["custom_fields"] = custom_data

    return {
        "row_num": row_num,
        "data": data,
        "errors": errors,
        "warnings": warnings,
        "valid": len(errors) == 0,
    }


async def parse_csv(
    content: bytes,
    event_id: uuid.UUID,
    db: AsyncSession,
    *,
    dob_format: str = "eu",  # v1.0.0o: "eu" or "iso" — disambiguates numeric dates where both first two components are ≤ 12.
) -> dict:
    """
    Parse and validate a CSV upload.

    Returns:
        {
            rows: [validated row dicts],
            summary: {total, valid, invalid, warnings},
            custom_fields: [{id, label, field_type, is_required}],
        }
    """
    # Load custom field definitions for this event
    result = await db.execute(
        select(CustomFieldDefinition)
        .where(CustomFieldDefinition.event_id == event_id)
        .order_by(CustomFieldDefinition.sort_order)
    )
    custom_fields: list[CustomFieldDefinition] = list(result.scalars().all())

    # Load existing participant emails for duplicate detection
    email_result = await db.execute(
        select(Participant.email).where(
            Participant.event_id == event_id,
            Participant.deleted_at.is_(None),
        )
    )
    existing_emails: set[str] = {row[0].lower() for row in email_result.fetchall()}

    # Parse CSV
    try:
        text = content.decode("utf-8-sig")  # handles BOM from Excel
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    rows = []
    seen_emails: set[str] = set()

    # v0.50f-4: build a header mapping so "First Name" / "first_name" /
    # "FIRST NAME" all map to the canonical 'first_name'. Custom-field
    # columns match by label. Unknown columns used to be silently dropped
    # — v0.85 #16 surfaces them so the importer can offer to auto-create
    # custom fields for them. Headers in IGNORED_HEADERS_NORMALISED
    # (export-only stuff like "No.", "Status", "Marks") are still
    # silently dropped.
    source_headers = reader.fieldnames or []
    header_mapping, unknown_headers = _build_row_mapper(source_headers, custom_fields)

    # v0.85 #16: for each unknown column, collect the per-row values so
    # the commit step can write them into the new custom field's blob.
    # Keyed by the source header string (the original column name).
    unknown_values_by_row: list[dict[str, str]] = []

    for row_num, raw in enumerate(reader, start=1):
        remapped = _remap_row(raw, header_mapping)
        # v0.83 #15: skip note rows — those starting with "#" in first_name.
        # The downloaded template includes such a row at the top with the
        # date format reminder. The example row beneath it is a real row
        # (Jane Smith) that the importer treats normally — admin is
        # expected to delete BOTH before importing real data.
        # v0.86 #16: note-row skip must NOT append to either rows[] or
        # unknown_values_by_row — keeping them aligned in length is what
        # commit_batch relies on to map values back to participants.
        first_name_check = (remapped.get("first_name") or "").strip()
        if first_name_check.startswith("#"):
            continue
        validated = _validate_row(
            row_num, remapped, custom_fields, seen_emails, existing_emails,
            dob_format=dob_format,
        )
        rows.append(validated)
        # Capture this row's values for unknown columns; the commit
        # step will turn these into custom_field values once the new
        # CustomFieldDefinition rows have ids.
        unknown_values_by_row.append({
            h: (raw.get(h) or "").strip() for h in unknown_headers
        })

    valid_count = sum(1 for r in rows if r["valid"])
    warning_count = sum(1 for r in rows if r["warnings"] and r["valid"])

    return {
        "rows": rows,
        "summary": {
            "total": len(rows),
            "valid": valid_count,
            "invalid": len(rows) - valid_count,
            "with_warnings": warning_count,
        },
        "custom_fields": [
            {
                "id": str(cf.id),
                "label": cf.label,
                "field_type": cf.field_type,
                "is_required": cf.is_required,
            }
            for cf in custom_fields
        ],
        # v0.85 #16: new-custom-field candidates and the per-row values.
        # The frontend preview should warn the admin: "These columns
        # aren't recognised — they will be added as custom fields, hidden
        # from the public registration form by default. Rename headers
        # to match existing fields if you'd rather not." On commit the
        # backend creates the CustomFieldDefinition rows and writes the
        # values into participants' custom_fields blobs.
        "new_custom_fields": unknown_headers,
        "unknown_values_by_row": unknown_values_by_row,
    }


def generate_template(custom_fields: list[CustomFieldDefinition]) -> str:
    """
    Generate a CSV template string with fixed columns + custom field columns.
    Returns the CSV content as a UTF-8 string (with BOM for Excel compatibility).

    v0.83 #15: the example row uses DD.MM.YYYY for the DOB so admins editing
    the template see the canonical date format inline. The UI hint near the
    Download Template button (in BatchRegisterModal) reinforces this. The
    parser is more lenient (accepts ISO 8601, slashes, dots, East-Asian
    formats), but DD.MM.YYYY is what the docs recommend and what the
    template demonstrates.
    """
    output = io.StringIO()
    cf_columns = [f"cf:{cf.id}" for cf in custom_fields]
    fieldnames = FIXED_COLUMNS + cf_columns

    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\r\n")
    writer.writeheader()

    # v0.83 #15: dedicated note row at the top of the template explaining
    # the expected date format. Most spreadsheet apps display this as a
    # full-width text row in the first cell, leaving subsequent cells
    # empty — which is harmless. The parser ignores rows where first_name
    # is empty (the first non-header position), so this row will be
    # quietly skipped on re-import. The "# " prefix is a visual cue
    # that this is a comment, not data.
    note_row: dict[str, str] = {col: "" for col in fieldnames}
    note_row["first_name"] = (
        "# Note: dates use DD.MM.YYYY (e.g. 15.01.1990). "
        "Delete this row and the example row below before importing."
    )
    writer.writerow(note_row)

    # Write a commented hint row using the first row as example data
    hint: dict[str, str] = {col: "" for col in fieldnames}
    hint["first_name"] = "Jane"
    hint["last_name"] = "Smith"
    hint["email"] = "jane.smith@example.com"
    hint["gender"] = "female"
    hint["date_of_birth"] = "15.01.1990"  # v0.83 #15: DD.MM.YYYY canonical
    hint["gdpr_consent"] = "true"
    for cf in custom_fields:
        if cf.field_type == "select":
            choices = (cf.options or {}).get("choices", [])
            hint[f"cf:{cf.id}"] = choices[0] if choices else ""
        elif cf.field_type == "boolean":
            hint[f"cf:{cf.id}"] = "true"
        elif cf.field_type == "number":
            hint[f"cf:{cf.id}"] = "0"
        elif cf.field_type == "date":
            hint[f"cf:{cf.id}"] = "01.01.2025"
        else:
            hint[f"cf:{cf.id}"] = f"example {cf.label}"
    writer.writerow(hint)

    return "\ufeff" + output.getvalue()  # UTF-8 BOM for Excel


async def commit_batch(
    rows: list[dict],
    event_id: uuid.UUID,
    db: AsyncSession,
    *,
    new_custom_fields: list[str] | None = None,
    unknown_values_by_row: list[dict[str, str]] | None = None,
) -> dict:
    """
    Commit pre-validated batch rows to the database.

    Only rows with valid=True are inserted. Invalid rows are counted as skipped.
    Per-row exceptions are caught and recorded — a single bad row does not abort
    the whole batch.

    v0.85 #16: when new_custom_fields is non-empty, the importer auto-creates
    one CustomFieldDefinition (text type, show_in_form=False) per unknown
    column before registering participants. Each row's value for those
    columns is then written into its custom_fields blob, keyed by the
    new definition's id. Admins can later promote any of these to the
    public registration form via the registration setup UI.

    Returns:
        {
            created: int,
            skipped: int,                   # invalid rows (errors present)
            failed: int,                    # valid rows that raised a DB exception
            errors: [{row_num, reason}],
            created_custom_fields: [        # v0.85 #16
                {id, label, field_type, show_in_form}
            ],
        }
    """
    from app.schemas.participant import ParticipantRegister
    from app.services.participant_service import register_participant

    new_custom_fields = new_custom_fields or []
    unknown_values_by_row = unknown_values_by_row or []

    # v0.85 #16: create the new custom field definitions first so the
    # ids exist before participant registration. Each gets show_in_form=False
    # (CSV-derived; admin can opt them into the form later). Sort_order
    # appended at the end so they don't reshuffle the existing form layout.
    created_custom_field_records: list[dict] = []
    label_to_id: dict[str, str] = {}
    if new_custom_fields:
        # Determine the next sort_order to append after
        existing_max_q = await db.execute(
            select(sa_func.coalesce(sa_func.max(CustomFieldDefinition.sort_order), 0))
            .where(CustomFieldDefinition.event_id == event_id)
        )
        next_sort_order = (existing_max_q.scalar() or 0) + 1
        for raw_label in new_custom_fields:
            label = raw_label.strip()
            if not label:
                continue
            cf = CustomFieldDefinition(
                event_id=event_id,
                label=label,
                field_type="text",         # safe default — admin can change later
                options=None,
                is_required=False,
                show_in_form=False,        # v0.85 #16: not on public form by default
                sort_order=next_sort_order,
            )
            db.add(cf)
            await db.flush()  # get cf.id
            label_to_id[raw_label] = str(cf.id)
            created_custom_field_records.append({
                "id": str(cf.id),
                "label": cf.label,
                "field_type": cf.field_type,
                "show_in_form": cf.show_in_form,
            })
            next_sort_order += 1
        # Commit the field-definition rows so they're visible to the
        # downstream register_participant calls (which read custom fields
        # for validation in some paths).
        await db.commit()

    created = 0
    skipped = 0
    failed = 0
    error_details: list[dict] = []

    # v0.86 #16: unknown_values_by_row is aligned 1:1 with rows[] by
    # contract — parse_csv only appends to both when a row is real
    # (note rows are skipped entirely). If the lengths somehow differ
    # (older frontend caching a stale preview, hand-crafted body, etc.),
    # fall back to empty per-row dicts to avoid stamping wrong values
    # onto wrong participants.
    aligned_unknown = unknown_values_by_row
    if len(aligned_unknown) != len(rows):
        aligned_unknown = [{} for _ in rows]

    for idx, row in enumerate(rows):
        if not row.get("valid", False):
            skipped += 1
            continue

        data = row["data"]
        row_num = row["row_num"]
        row_unknown = aligned_unknown[idx] if idx < len(aligned_unknown) else {}

        # v0.85 #16: merge unknown-column values into custom_fields blob,
        # keyed by the newly-created definition ids.
        existing_cfs = dict(data.get("custom_fields") or {})
        for src_label, value in row_unknown.items():
            new_id = label_to_id.get(src_label)
            if new_id and value:
                existing_cfs[new_id] = value

        try:
            payload = ParticipantRegister(
                first_name=data["first_name"],
                last_name=data["last_name"],
                email=data["email"],
                gender=data.get("gender"),
                date_of_birth=data.get("date_of_birth"),
                phone=data.get("phone"),
                address=data.get("address"),
                country=data.get("country"),
                church_organisation=data.get("church_organisation"),
                group_code=data.get("group_code"),
                gdpr_consent=data.get("gdpr_consent", False),
                custom_fields=existing_cfs or None,
            )
            await register_participant(db, event_id, payload)
            await db.commit()
            created += 1

        except Exception as exc:  # noqa: BLE001
            await db.rollback()
            failed += 1
            error_details.append({"row_num": row_num, "reason": str(exc)})

    return {
        "created": created,
        "skipped": skipped,
        "failed": failed,
        "errors": error_details,
        "created_custom_fields": created_custom_field_records,
    }
