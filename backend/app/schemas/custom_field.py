"""Custom field definition schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class CustomFieldCreate(BaseModel):
    label: str
    field_type: str = "text"  # text | number | select | boolean | date
    options: list[str] | None = None  # for select type
    is_required: bool = False
    sort_order: int = 0
    # v0.85 #16: defaults True for fields created via the registration setup
    # UI (the typical path). The CSV importer overrides to False for fields
    # synthesised from unknown columns.
    show_in_form: bool = True


class CustomFieldUpdate(BaseModel):
    label: str | None = None
    field_type: str | None = None
    options: list[str] | None = None
    is_required: bool | None = None
    sort_order: int | None = None
    show_in_form: bool | None = None


class CustomFieldResponse(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    label: str
    field_type: str
    options: dict | None
    is_required: bool
    sort_order: int
    show_in_form: bool
    created_at: datetime

    model_config = {"from_attributes": True}
