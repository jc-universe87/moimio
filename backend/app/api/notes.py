"""Notes routes — CRUD for notes on any entity."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User, UserRole
from app.models.note import Note
from app.api.deps import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix="/api/notes", tags=["notes"])


class NoteCreate(BaseModel):
    notable_type: str
    notable_id: uuid.UUID
    content: str
    is_published: bool = False


class NoteResponse(BaseModel):
    id: uuid.UUID
    notable_type: str
    notable_id: uuid.UUID
    content: str
    is_published: bool
    author_id: uuid.UUID
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


@router.get("/")
async def list_notes(
    notable_type: str = Query(...),
    notable_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List notes for an entity. Shows private (own) + published notes."""
    result = await db.execute(
        select(Note).where(
            Note.notable_type == notable_type,
            Note.notable_id == notable_id,
        ).order_by(Note.created_at.desc())
    )
    all_notes = list(result.scalars().all())

    # Filter: show published notes + own private notes
    visible = [
        n for n in all_notes
        if n.is_published or n.author_id == current_user.id
    ]

    return [
        {
            "id": n.id, "notable_type": n.notable_type, "notable_id": n.notable_id,
            "content": n.content, "is_published": n.is_published,
            "author_id": n.author_id,
            "created_at": n.created_at.isoformat() if n.created_at else "",
            "updated_at": n.updated_at.isoformat() if n.updated_at else "",
        }
        for n in visible
    ]


@router.post("/", status_code=201)
async def create_note(
    data: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a note attached to any entity."""
    note = Note(
        notable_type=data.notable_type,
        notable_id=data.notable_id,
        content=data.content,
        is_published=data.is_published,
        author_id=current_user.id,
    )
    db.add(note)
    await db.flush()
    await db.refresh(note)
    logger.info("note_created", note_id=str(note.id), type=data.notable_type)
    return {
        "id": note.id, "notable_type": note.notable_type, "notable_id": note.notable_id,
        "content": note.content, "is_published": note.is_published,
        "author_id": note.author_id,
        "created_at": note.created_at.isoformat(), "updated_at": note.updated_at.isoformat(),
    }


@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a note. Only the author or a Super Admin can delete.

    v0.50j: previously allowed system-level event_admin too. With that
    role removed, we keep this conservative: author-or-SuperAdmin. If
    a per-event admin needs to delete someone else's note, ask a Super
    Admin or have the note author do it.
    """
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail={"key": "errors.notes.not_found"})
    if note.author_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail={"key": "errors.notes.delete_forbidden"})
    await db.delete(note)
    await db.flush()
    logger.info("note_deleted", note_id=str(note_id))


@router.get("/counts")
async def note_counts(
    event_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get note counts for all entities in an event.
    Only counts notes visible to the current user: published notes + own private notes.
    Returns { "type:id": count }.
    """
    from sqlalchemy import func as sqlfunc, or_
    result = await db.execute(
        select(Note.notable_type, Note.notable_id, sqlfunc.count(Note.id))
        .where(or_(Note.is_published == True, Note.author_id == current_user.id))
        .group_by(Note.notable_type, Note.notable_id)
    )
    counts = {}
    for notable_type, notable_id, count in result.all():
        counts[f"{notable_type}:{notable_id}"] = count
    return counts
