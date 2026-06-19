"""Capabilities endpoint (v1.0.0g).

Frontend reads `GET /api/capabilities` on boot to know which features
the running instance has enabled. Used to hide nav entries, suppress
buttons, and avoid 404s when a capability flag is off.

This is a small surface deliberately — capability decisions live in
env vars, not in the database, so the response is essentially a
declassification of `core/config.py` for the frontend.

Public endpoint (no auth required): the frontend may call this before
login to know whether to render allocation-related preview surfaces.
The information is non-sensitive — knowing whether a feature is
enabled doesn't help an attacker.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings


router = APIRouter(tags=["capabilities"])


class CapabilitiesResponse(BaseModel):
    allocation: bool
    outbound_webhooks: bool
    # v1.0.0h: when true, the frontend should call GET /api/billing-info
    # before completing event creation and show a confirmation dialog
    # rendering the returned amount/currency/card-last-4.
    create_event_confirmation: bool
    # v1.0.0aa: the SaaS account-portal URL. Empty for self-hosters; when
    # set, CE shows a "Manage account" link in the admin sidebar. A value,
    # not a mode flag — CE renders the link if given one. Non-sensitive
    # (the portal itself is behind its own magic-link sign-in).
    account_url: str = ""


@router.get("/api/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities() -> CapabilitiesResponse:
    settings = get_settings()
    return CapabilitiesResponse(
        allocation=settings.feature_allocation,
        outbound_webhooks=settings.feature_outbound_webhooks,
        create_event_confirmation=settings.feature_create_event_confirmation,
        account_url=settings.account_url,
    )
