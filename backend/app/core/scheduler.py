"""Background scheduler (v1.0.0g).

APScheduler with AsyncIOScheduler runs jobs inside FastAPI's event loop,
so jobs share the async SQLAlchemy session machinery without thread-
safety concerns.

Two jobs:
  - `retry-webhooks` (every 30s): processes PENDING outbound webhook
    deliveries whose `next_attempt_at <= now`. Bounded batch size keeps
    a tick latency-cheap when the queue is empty.
  - `prune-webhook-deliveries` (daily 03:00 UTC): deletes delivery log
    rows older than retention.

The scheduler is started by the FastAPI lifespan and stopped on
shutdown. It is a no-op when FEATURE_OUTBOUND_WEBHOOKS is off — the
jobs are not registered.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.core.logging import get_logger
from app.services import webhook_service


log = get_logger(__name__)

# Module-level scheduler so start/stop can be called from lifespan.
_scheduler: AsyncIOScheduler | None = None


async def _retry_webhooks_job() -> None:
    """Process all due PENDING outbound webhook deliveries."""
    async with async_session_factory() as db:
        try:
            n = await webhook_service.process_pending_deliveries(db)
            if n > 0:
                log.info("webhook_retry_job.processed", n=n)
        except Exception:
            log.exception("webhook_retry_job.failed")


async def _prune_webhook_deliveries_job() -> None:
    """Drop delivery rows older than retention window."""
    settings = get_settings()
    async with async_session_factory() as db:
        try:
            await webhook_service.prune_old_deliveries(
                db, retention_days=settings.webhook_delivery_retention_days
            )
        except Exception:
            log.exception("webhook_prune_job.failed")


def start_scheduler() -> AsyncIOScheduler:
    """Create, configure, and start the scheduler. Idempotent."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return _scheduler

    settings = get_settings()
    scheduler = AsyncIOScheduler(timezone="UTC")

    if settings.feature_outbound_webhooks:
        scheduler.add_job(
            _retry_webhooks_job,
            trigger=IntervalTrigger(seconds=30),
            id="retry-webhooks",
            max_instances=1,
            coalesce=True,  # if a tick is missed, run once not many times
            misfire_grace_time=60,
        )
        scheduler.add_job(
            _prune_webhook_deliveries_job,
            trigger=CronTrigger(hour=3, minute=0, timezone="UTC"),
            id="prune-webhook-deliveries",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
        )

    scheduler.start()
    log.info(
        "scheduler.started",
        jobs=[j.id for j in scheduler.get_jobs()],
        feature_outbound_webhooks=settings.feature_outbound_webhooks,
    )
    _scheduler = scheduler
    return scheduler


async def stop_scheduler() -> None:
    """Stop the scheduler if running. Used by FastAPI shutdown."""
    global _scheduler
    if _scheduler is None:
        return
    try:
        _scheduler.shutdown(wait=False)
        log.info("scheduler.stopped")
    except Exception:
        log.exception("scheduler.stop_failed")
    finally:
        _scheduler = None
