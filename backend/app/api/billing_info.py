"""Billing-info endpoint (v1.0.0h; credit model v1.0.0w).

Frontend calls GET /api/billing-info when
`capabilities.create_event_confirmation` is true. Under the prepaid-
credit model (v1.0.0w) it returns one field, `buy_credit_url`: where the
"buy a credit" button in CE's out-of-credits notice should point. The
SaaS sets it per tenant; empty means "no self-serve link" and CE omits
the button. Auth required because the link is tenant-specific.

History: before v1.0.0w this returned a charge amount, currency, and card
last-four for a charge-on-creation model that product policy v1 replaced
with prepaid credits.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.models.user import User


router = APIRouter(tags=["billing-info"])


class BillingInfoResponse(BaseModel):
    # Where "buy a credit" points. Empty string = no link configured,
    # and CE hides the button rather than rendering a dead one.
    buy_credit_url: str


@router.get("/api/billing-info", response_model=BillingInfoResponse)
async def get_billing_info(
    current_user: User = Depends(get_current_user),
) -> BillingInfoResponse:
    settings = get_settings()
    return BillingInfoResponse(buy_credit_url=settings.buy_credit_url)
