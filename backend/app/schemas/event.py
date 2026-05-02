"""Event request/response schemas."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel


class EventCreate(BaseModel):
    name: str
    description: str | None = None
    location: str | None = None
    timezone: str | None = None  # IANA name, defaults to 'UTC' server-side
    start_date: date | None = None
    end_date: date | None = None
    # v0.51: duplicate-from-source. When set, server-side copies config
    # tables (marks, field configs, custom fields, allocation categories +
    # units, staff assignments) from the source event after insert. Skips
    # the default field-config + default-category scaffolding since the
    # source event already has those. Caller must have access to source.
    copy_from_event_id: uuid.UUID | None = None


class EventUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    location: str | None = None
    timezone: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = None
    settings: dict | None = None
    # Setup hub gate flags. Usually set via dedicated confirm endpoints,
    # but exposed here for completeness and for the "un-confirm on edit"
    # path handled in the service layer.
    details_confirmed: bool | None = None
    registration_confirmed: bool | None = None


class EventResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    location: str | None
    timezone: str
    start_date: date | None
    end_date: date | None
    status: str
    details_confirmed: bool
    registration_confirmed: bool
    is_archived: bool = False  # v0.50i
    settings: dict | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    # v0.50h: optional at-a-glance counts for the redesigned events list.
    # Populated by the list endpoint; omitted/None on single-event GET.
    participant_count: int | None = None
    checked_in_count: int | None = None

    model_config = {"from_attributes": True}


class FieldConfigItem(BaseModel):
    field_name: str
    is_enabled: bool = False
    is_required: bool = False


class FieldConfigResponse(BaseModel):
    id: uuid.UUID
    field_name: str
    is_enabled: bool
    is_required: bool

    model_config = {"from_attributes": True}
