"""Participant request/response schemas."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr
from typing import Any


class ParticipantRegister(BaseModel):
    """Public registration form submission."""
    first_name: str
    last_name: str
    email: EmailStr
    gender: str | None = None
    date_of_birth: date | None = None
    phone: str | None = None
    address: str | None = None
    country: str | None = None
    church_organisation: str | None = None
    message: str | None = None
    group_code: str | None = None
    group_code_categories: list[str] | None = None  # None = all categories
    gdpr_consent: bool
    preferred_language: str | None = 'en'
    custom_fields: dict[str, str] | None = None
    preference_requests: list[dict[str, Any]] | None = None  # list of preference objects


class ParticipantUpdate(BaseModel):
    """Admin update of a participant."""
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    phone: str | None = None
    address: str | None = None
    country: str | None = None
    church_organisation: str | None = None
    message: str | None = None
    group_code: str | None = None
    group_code_categories: list[str] | None = None
    override_group_room: bool | None = None
    registration_status: str | None = None
    # v0.85 #16: custom-field updates from the People table inline editor.
    # Maps custom_field_definition.id (str-uuid) to its new string value.
    # When provided, the dict REPLACES the existing custom_fields blob —
    # caller is expected to merge first if a partial update is intended.
    # v0.91 #14 (clear bug): values are `str | None` — null clears the
    # field (deletes the CustomFieldValue row server-side). Was strictly
    # `dict[str, str]` which Pydantic rejected nulls on, so the frontend's
    # clear-to-null requests were 422'd silently and the modal closed
    # showing no change.
    custom_fields: dict[str, str | None] | None = None


class GroupCodeUpdate(BaseModel):
    """Reassign a participant's group code."""
    group_code: str
    group_code_categories: list[str] | None = None


class CheckInRequest(BaseModel):
    checked_in: bool = True


class ParticipantResponse(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    gender: str | None
    date_of_birth: date | None
    phone: str | None
    address: str | None
    country: str | None
    church_organisation: str | None
    message: str | None
    group_code: str | None
    group_code_categories: list | None
    participant_number: int | None
    override_group_room: bool = False
    registration_status: str
    gdpr_consent: bool
    checked_in: bool
    checked_in_at: datetime | None
    created_at: datetime
    updated_at: datetime
    preferred_language: str = 'en'
    custom_fields: dict[str, str] = {}

    model_config = {"from_attributes": True}
