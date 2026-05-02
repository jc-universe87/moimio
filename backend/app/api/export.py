"""Export routes — CSV download with allocation data, PDF rosters per category.

v0.50f-3 permission enforcement
───────────────────────────────
- participants.csv                       → `people: read` (contains PII)
- category/{id}/pdf ?format=compact|signin → `reports: read` (aggregate rosters)
- category/{id}/pdf ?format=detailed     → `people: read` (contains PII)
- backup.zip                             → admin-only (full DB dump)

Principle: reports are anonymised aggregates; anything with PII is under
`people` permission, matching how the participant list itself is gated.

Behaviour before v0.50f-3: all three were admin-only, so the `reports`
permission added in v0.50e-1d was shape-only. This closes that loop.
"""

import csv
import io
import uuid

from app.core.exceptions import MoimioAppError
from fpdf.errors import FPDFException
from fastapi import APIRouter, Depends, File, HTTPException, status, UploadFile
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User, UserRole
from app.api.deps import require_role, get_current_user, require_event_admin_dep
from app.services.event_service import get_event_by_id
from app.services.participant_service import list_participants
from app.services.allocation_service import (
    list_categories, get_allocations_by_category, list_units, get_category,
    get_all_allocations,
)
from app.services.pdf_service import generate_category_pdf, RENDERERS
from app.services.permissions import get_event_permissions, has_read
from app.models.custom_field import CustomFieldDefinition
from app.models.allocation_unit import AllocationUnit
# v1.0-pre #30: marks in CSV export — included as a comma-separated names
# column so admins exporting the People list see participant tags too.
from app.models.mark import MarkAssignment, MarkDefinition
from sqlalchemy import select as sa_select

router = APIRouter(prefix="/api/events/{event_id}/export", tags=["export"])


# ─── Permission guards ───

async def _require_people_read(db: AsyncSession, user: User, event_id: uuid.UUID):
    """Admin OR staff with `people: read` (or write)."""
    if user.role == UserRole.SUPER_ADMIN:
        return
    perms = await get_event_permissions(db, user, event_id)
    if perms is None or not has_read(perms, "people"):
        raise HTTPException(status_code=403, detail={"key": "errors.export.people_read_required"})


async def _require_reports_read(db: AsyncSession, user: User, event_id: uuid.UUID):
    """Admin OR staff with `reports: read`."""
    if user.role == UserRole.SUPER_ADMIN:
        return
    perms = await get_event_permissions(db, user, event_id)
    if perms is None or not has_read(perms, "reports"):
        raise HTTPException(status_code=403, detail={"key": "errors.stats.read_required"})


@router.get("/participants.csv")
async def export_participants_csv(
    event_id: uuid.UUID,
    mode: str = "full",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export all participants as CSV with allocation assignments.

    v0.50f-3: requires `people: read` (admin also qualifies). The CSV
    contains PII so it's gated by the same permission that governs the
    participant list.

    Query params:
      mode  — `full` (default) emits all columns including allocations,
              custom fields, and message. `emails` emits a minimal
              two-column file (Name, Email) suitable for pasting into
              a mailing-list tool. Unknown values fall back to `full`.
    """
    await _require_people_read(db, current_user, event_id)
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail={"key": "errors.event.not_found"})

    participants = await list_participants(db, event_id)

    # Emails-only mode: short-circuit before the heavier allocation +
    # custom-field lookups. Excludes participants with no email (shouldn't
    # happen since email is required at registration, but defensive).
    if mode == "emails":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Name", "Email"])
        for p in participants:
            if not p.email:
                continue
            full_name = f"{p.first_name or ''} {p.last_name or ''}".strip()
            writer.writerow([full_name, p.email])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=emails_{event_id}.csv"},
        )

    # v1.0-pre #17: dropped the per-category allocation columns from
    # participants.csv. The People page CSV export is participant-data
    # only — allocations live on the Reports / Organise side. The
    # backend variables that fetched and assembled allocation columns
    # have been removed too; if you need allocations as a flat export,
    # the per-category PDFs and the in-app backup ZIP both cover it.

    # v1.0-pre #30: marks as a comma-separated names column.
    # Build a {participant_id_str: [mark_name,...]} lookup. Order
    # follows MarkAssignment insertion which is roughly chronological.
    marks_lookup: dict[str, list[str]] = {}
    if participants:
        from sqlalchemy import select as sa_select_marks  # local alias to avoid shadow
        ma_q = await db.execute(
            sa_select_marks(MarkAssignment, MarkDefinition)
            .join(MarkDefinition, MarkAssignment.mark_id == MarkDefinition.id)
            .where(MarkAssignment.event_id == event_id)
        )
        for ma, md in ma_q.all():
            marks_lookup.setdefault(str(ma.participant_id), []).append(md.name)

    output = io.StringIO()
    writer = csv.writer(output)

    # v0.50f-4: load custom field definitions so we can emit their values
    # as named columns, preserving full participant data for round-trip
    # backup/restore.
    cf_result = await db.execute(
        sa_select(CustomFieldDefinition)
        .where(CustomFieldDefinition.event_id == event_id)
        .order_by(CustomFieldDefinition.sort_order)
    )
    custom_fields: list[CustomFieldDefinition] = list(cf_result.scalars().all())

    # Header — fixed columns first, then a marks column, then custom
    # fields, then message. Allocation columns are deliberately dropped
    # in v1.0-pre #17 — see comment above.
    # v0.50f-4: added "GDPR Consent" for round-trip integrity.
    header = [
        "First Name", "Last Name", "Email", "Gender",
        "Date of Birth", "Phone", "Address", "Country",
        "Church/Organisation", "Group Code", "GDPR Consent",
        "No.", "Status", "Checked In",
        "Marks",
    ]
    for cf in custom_fields:
        header.append(cf.label)
    header.append("Message")
    writer.writerow(header)

    for p in participants:
        row = [
            p.first_name, p.last_name, p.email or "", p.gender or "",
            str(p.date_of_birth) if p.date_of_birth else "", p.phone or "",
            p.address or "", p.country or "", p.church_organisation or "",
            p.group_code or "",
            "true" if p.gdpr_consent else "false",
            str(p.participant_number) if p.participant_number else "",
            p.registration_status.value if p.registration_status else "",
            "Yes" if p.checked_in else "No",
            ", ".join(marks_lookup.get(str(p.id), [])),
        ]
        # Emit custom-field values by field id lookup
        cf_values = p.custom_fields  # {str(field_id): value}
        for cf in custom_fields:
            row.append(cf_values.get(str(cf.id), "") or "")
        row.append(p.message or "")
        writer.writerow(row)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=participants_{event_id}.csv"},
    )


@router.get("/category/{category_id}/pdf")
async def export_category_pdf(
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    format: str = "compact",
    with_cover: bool = False,
    lang: str = "en",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a PDF roster for one allocation category.

    v0.50f-3 permission model:
      - `compact` and `signin` formats → aggregate rosters; `reports: read`
      - `detailed` format → contains PII; `people: read`
    Admin bypasses both.

    Query params:
      format      — layout: compact | detailed | signin (default compact)
      with_cover  — include an optional cover page with event stats (v0.50k)
      lang        — PDF language, independent of UI language (v0.50o).
                    One of 'en', 'de', 'ko', 'es', 'pt-BR', 'fr'.
                    Unknown values fall back to English.
    """
    if format == "detailed":
        await _require_people_read(db, current_user, event_id)
    else:
        await _require_reports_read(db, current_user, event_id)
    if format not in RENDERERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"key": "errors.export.unknown_format", "params": {"format": format, "allowed": ", ".join(RENDERERS.keys())}},
        )

    # ── Pre-flight checks — return clear 400s instead of cryptic 500s ──
    category = await get_category(db, category_id)
    if not category or category.event_id != event_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.allocation.group_type_not_found"})

    units = await list_units(db, category_id)
    if not units:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"key": "errors.allocation.no_units"},
        )

    allocations = await get_allocations_by_category(db, category_id)
    total_allocated = sum(len(members) for members in allocations.values())
    participants = await list_participants(db, event_id)
    confirmed = [p for p in participants if p.registration_status and p.registration_status.value != "cancelled"]
    if not confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"key": "errors.export.no_confirmed_participants"},
        )
    if total_allocated == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"key": "errors.export.no_allocated_participants"},
        )

    try:
        pdf_bytes = await generate_category_pdf(
            db, event_id, category_id, format,
            with_cover=with_cover,
            exported_by=current_user.full_name,
            lang=lang,
        )
    except MoimioAppError:
        raise  # let the global handler convert to dict-detail
    except FPDFException as e:
        # v0.70d-3c-9: dedicated key for font-related FPDF failures.
        # v0.70d-3c-10: Nunito is now bundled in-repo at
        # backend/app/fonts/, so missing-weight crashes (DejaVu's
        # italic file shipped only in `fonts-dejavu-extra`, not
        # `-core`) are eliminated. The catch stays defensive — any
        # future font issue (corrupt file, OS-level removal, CJK
        # fallback path failing on exotic glyphs) still surfaces a
        # translated message instead of a raw English exception.
        import traceback
        print(f"[PDF FONT ERROR] {type(e).__name__}: {e}\n{traceback.format_exc()}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"key": "errors.export.pdf_font_missing", "params": {"detail": str(e)}},
        )
    except Exception as e:
        # Log full traceback to backend logs and return the actual error in the response
        # so the admin user can see what went wrong rather than a generic 500.
        import traceback
        tb = traceback.format_exc()
        print(f"[PDF EXPORT ERROR] {type(e).__name__}: {e}\n{tb}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"key": "errors.export.pdf_generation_failed", "params": {"detail": f"{type(e).__name__}: {e}"}},
        )

    if pdf_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"key": "errors.export.event_or_category_not_found"},
        )

    # v0.50o: filename includes the PDF language code so downloads of the
    # same roster in different languages don't overwrite each other in the
    # user's Downloads folder. Frontend builds its own slug-based filename,
    # but this server-side fallback matters when the endpoint is hit
    # directly (curl/scripts/email attachments).
    filename = f"roster_{format}_{category_id}_{lang}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/backup.zip")
async def export_backup_zip(
    event_id: uuid.UUID,
    mode: str = "full",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    """
    Download an event backup as a ZIP file.

    Query params:
      mode — "full" (default) includes all data: participants, allocations,
             mark assignments, preferences, custom field values.
             "structure" is a GDPR-safe template: event settings, categories,
             units, custom field DEFINITIONS, mark DEFINITIONS, field
             configs, event-level notes. No PII, no participant-linked
             records. Suitable for sharing an event template between
             organisations or archiving a "shape" without personal data.

    Event Admin only.
    """
    from app.services.backup_service import export_event_zip

    if mode not in ("full", "structure"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"key": "errors.export.unknown_backup_mode", "params": {"mode": mode, "allowed": "full, structure"}},
        )

    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail={"key": "errors.event.not_found"})

    try:
        zip_bytes = await export_event_zip(event_id, db, mode=mode)
    except MoimioAppError:
        raise  # let the global handler convert to dict-detail
    except Exception as e:
        import traceback
        print(f"[BACKUP EXPORT ERROR] {type(e).__name__}: {e}\n{traceback.format_exc()}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"key": "errors.export.backup_failed", "params": {"detail": f"{type(e).__name__}: {e}"}},
        )

    safe_name = event.name.replace(" ", "_").replace("/", "-")[:40]
    from datetime import date
    datestamp = date.today().isoformat()
    # v0.50r: structure backups get a "-structure" suffix so organisers
    # can tell at a glance which kind of file they have — especially
    # important when sharing with external parties.
    suffix = "-structure" if mode == "structure" else ""
    filename = f"moimio-backup{suffix}-{safe_name}-{datestamp}.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Restore endpoints ─────────────────────────────────────────────────────────

restore_router = APIRouter(prefix="/api/events", tags=["export"])


@restore_router.post("/restore/preview")
async def restore_preview(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
):
    """
    Upload a backup ZIP and receive a summary without creating anything.
    Super Admin only.
    """
    from app.services.backup_service import preview_restore

    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail={"key": "errors.export.empty_file"})

    summary = preview_restore(content)
    return summary


@restore_router.post("/restore/confirm", status_code=201)
async def restore_confirm(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
):
    """
    Upload a backup ZIP and create a new event with all its data.
    The restored event is named '<original name> (Restored)' and set to DRAFT.
    Super Admin only.
    """
    from app.services.backup_service import confirm_restore

    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail={"key": "errors.export.empty_file"})

    try:
        result = await confirm_restore(content, db)
    except MoimioAppError:
        raise  # let the global handler convert to dict-detail
    except Exception as e:
        import traceback
        print(f"[RESTORE ERROR] {type(e).__name__}: {e}\n{traceback.format_exc()}", flush=True)
        raise HTTPException(
            status_code=500,
            detail={"key": "errors.export.restore_failed", "params": {"detail": f"{type(e).__name__}: {e}"}},
        )

    return result
