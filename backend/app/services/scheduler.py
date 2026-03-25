import asyncio

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.quality import generate_quality_metrics


async def quality_metrics_scheduler() -> None:
    interval_seconds = max(settings.quality_metrics_interval_hours, 1) * 3600
    while True:
        db = SessionLocal()
        try:
            generate_quality_metrics(db)
        finally:
            db.close()
        await asyncio.sleep(interval_seconds)
