import asyncio

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.backup import run_db_backup
from app.services.quality import generate_quality_metrics


async def quality_metrics_scheduler() -> None:
    interval_seconds = max(settings.quality_metrics_interval_hours, 1) * 3600
    while True:
        db = SessionLocal()
        try:
            generate_quality_metrics(db)
        except Exception as e:
            print(f"Quality Metrics Scheduler Error: {e}")
        finally:
            db.close()
        await asyncio.sleep(interval_seconds)


async def daily_backup_scheduler() -> None:
    interval_seconds = 24 * 3600
    while True:
        try:
            run_db_backup()
        except Exception as e:
            print(f"Daily Backup Scheduler Error: {e}")
        await asyncio.sleep(interval_seconds)
