"""Billing-info endpoint (v1.0.0h).

Frontend calls GET /api/billing-info when
`capabilities.create_event_confirmation` is true, to render the
"are you sure?" confirmation dialog before event creation.

Returns the three values from env (EVENT_CHARGE_AMOUNT,
EVENT_CHARGE_CURRENCY, BILLING_CARD_LAST4). Missing values are
returned as empty strings; the frontend handles fallback wording.

Auth required: a card last-4 is customer data, even though it's just
four digits. The full PAN never lives in CE config — see the .env.example
note on BILLING_CARD_LAST4. Returning empty strings rather than
nulls keeps the response shape stable for the frontend's i18n
templates.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.models.user import User


router = APIRouter(tags=["billing-info"])


class BillingInfoResponse(BaseModel):
    amount: str       # e.g. "120" — empty string if not configured
    currency: str     # e.g. "EUR" — empty string if not configured
    card_last4: str   # e.g. "4242" — empty string if not configured


@router.get("/api/billing-info", response_model=BillingInfoResponse)
async def get_billing_info(
    current_user: User = Depends(get_current_user),
) -> BillingInfoResponse:
    settings = get_settings()
    return BillingInfoResponse(
        amount=settings.event_charge_amount,
        currency=settings.event_charge_currency,
        card_last4=settings.billing_card_last4,
    )
