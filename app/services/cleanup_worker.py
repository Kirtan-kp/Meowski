import asyncio
import logging

from app.services.cleanup_service import CleanupService
from app.core.config import settings


logger = logging.getLogger(__name__)


async def cleanup_worker(cleanup_service: CleanupService):
    while True:
        try:
            result = await asyncio.to_thread(
                cleanup_service.cleanup
            )

            if result["expired_files"] or result["expired_sessions"]:
                logger.info(
                    "Cleanup completed: expired_files=%d expired_sessions=%d",
                    len(result["expired_files"]),
                    len(result["expired_sessions"]),
                )

        except asyncio.CancelledError:
            logger.info("Cleanup worker stopped")
            raise

        except Exception:
            logger.exception("Cleanup worker failed")

        await asyncio.sleep(settings.cleanup_interval_seconds)