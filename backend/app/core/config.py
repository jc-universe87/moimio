"""Application configuration via environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ─── Database ───
    database_url: str = "postgresql+asyncpg://moimio:moimio_dev@db:5432/moimio"

    # ─── Auth ───
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 1440  # 24 hours
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # ─── App ───
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:6120"
    rate_limit_registration: int = 10

    # ─── Capability flags (v1.0.0g) ───
    #
    # Capability-not-commercial naming. CE does not know which capabilities
    # are "premium" — these are framed as generic toggles that any
    # self-hoster might legitimately want. SaaS sets per-tenant values via
    # the standard env-var surface; CE never gains tier awareness.
    #
    # FEATURE_ALLOCATION: when false, the allocation engine and its router
    # are excluded entirely. Bucket 4 §2: enables a registration-only
    # deployment for SaaS Registration tier and for self-hosters who don't
    # need group/room assignment.
    #
    # FEATURE_OUTBOUND_WEBHOOKS: when false, the outbound webhook
    # subsystem (admin UI, router, scheduler jobs) is hidden. Default ON
    # so self-hosters get the integration capability; SaaS can opt out
    # per tenant if a tier shouldn't expose it.
    feature_allocation: bool = True
    feature_outbound_webhooks: bool = True

    # ─── Create-event confirmation (v1.0.0h) ───
    #
    # When true, the event-create flow surfaces a confirmation dialog
    # before completing the POST. The dialog renders the three billing-
    # info values below (amount + currency + card last-4) so the admin
    # sees what will be charged before committing.
    #
    # CE default: false. Self-hosters never see a dialog. SaaS sets
    # this to true at provisioning for tenants on the per-event plan.
    #
    # Capability-not-commercial naming: this flag describes the UI
    # capability (a confirmation step), not why a commercial provider
    # would want it (billing).
    feature_create_event_confirmation: bool = False

    # Supporting data for the confirmation dialog. Read at runtime via
    # GET /api/billing-info so the frontend doesn't need a rebuild when
    # values change — SaaS just updates the env vars and restarts the
    # container. All three are independent: if a value is missing, the
    # dialog falls back gracefully (e.g. card last-4 missing → "your
    # card on file" instead of "card ending YYYY").
    event_charge_amount: str = ""        # e.g. "120" — string so the frontend's Intl can format
    event_charge_currency: str = ""      # e.g. "EUR", "GBP", "KRW" — ISO 4217
    billing_card_last4: str = ""         # e.g. "4242" — last 4 digits only, never the full PAN

    # ─── Tenant identity (v1.0.0h) ───
    #
    # Optional. When set, the value is stamped onto every outbound
    # webhook envelope as a top-level `tenant_id` field. When empty,
    # the field is omitted entirely — self-hosters never see it in
    # their payloads. SaaS provisioning sets this per-tenant at install
    # time so its receiver can route incoming webhooks to the right
    # customer record. CE doesn't interpret the value; it's an opaque
    # string chosen by whoever is provisioning the install.
    moimio_tenant_id: str = ""

    # ─── SaaS-managed webhook auto-registration (v1.0.0g) ───
    #
    # When both env vars are set at first boot AND no outbound webhook
    # endpoints exist yet, CE auto-creates a SaaS-managed endpoint
    # subscribing to all event types. The endpoint is flagged
    # `managed_by="saas"` and is hidden from the admin UI; self-hosters
    # never see it because they never set these env vars.
    #
    # Bucket 4 §1 reinforcement: CE doesn't know SaaS exists. These env
    # vars are framed as "automatic webhook configuration via environment"
    # — a feature self-hosters with deployment automation might also use.
    moimio_webhook_url: str = ""
    moimio_webhook_secret: str = ""

    # ─── Outbound webhook delivery log retention (v1.0.0g) ───
    #
    # The `outbound_webhook_deliveries` table grows with every webhook
    # attempt. 30 days is enough for any practical debugging conversation
    # and keeps the table small. Pruned daily by a scheduled job.
    webhook_delivery_retention_days: int = 30

    # NOTE: v0.61b-2 removed the `app_url` setting. Public URLs for email
    # links (registration confirmation, password reset) are now derived
    # from the incoming request via app.core.urls.get_app_base_url, so
    # self-hosters on different domains and future multi-domain SaaS
    # deployments don't need to pin a canonical URL in .env. Any lingering
    # APP_URL=... line in an existing .env file is silently ignored by
    # pydantic-settings and can be removed.

    # ─── Email (SMTP) ───
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Moimio"
    smtp_tls: bool = True       # STARTTLS on port 587
    smtp_ssl: bool = False      # Implicit SSL on port 465

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.smtp_host and self.smtp_user)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
