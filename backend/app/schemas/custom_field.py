"""Custom field definition schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CustomFieldCreate(BaseModel):
    label: str
    field_type: str = "text"  # text | number | select | boolean | date | info
    options: list[str] | None = None  # for select type
    # v1.0.7: the organiser's text, for the info type.
    info_text: str | None = Field(default=None, max_length=5000)
    is_required: bool = False
    # v1.0.7: None puts the new field at the end of the form.
    sort_order: int | None = None
    # v0.85 #16: defaults True for fields created via the registration setup
    # UI (the typical path). The CSV importer overrides to False for fields
    # synthesised from unknown columns.
    show_in_form: bool = True
    # v1.0.7: shown only when an earlier answer matches. Shapes in
    # app/services/field_conditions.py.
    show_if: dict | None = None


class CustomFieldUpdate(BaseModel):
    label: str | None = None
    field_type: str | None = None
    options: list[str] | None = None
    info_text: str | None = Field(default=None, max_length=5000)
    is_required: bool | None = None
    sort_order: int | None = None
    show_in_form: bool | None = None
    # Sending null removes the rule; leaving it out keeps it.
    show_if: dict | None = None


class CustomFieldReorder(BaseModel):
    # Every field of the event, in the new order.
    field_ids: list[uuid.UUID]


class CustomFieldResponse(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    label: str
    field_type: str
    options: dict | None
    is_required: bool
    sort_order: int
    show_in_form: bool
    show_if: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
