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
