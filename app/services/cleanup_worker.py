import asyncio
import logging
from app.db.databse import SessionLocal
from app.services.cleanup_service import CleanupService
from app.core.config import settings
from app.api.dependencies import (
    get_bm25_index_service,
    get_retrieval_cache_service,
    get_session_state_service,
    get_vector_store,
)

logger = logging.getLogger(__name__)

def _run_cleanup_cycle():
    db = SessionLocal()
    try:
        cleanup_service = CleanupService(
            db=db,
            vector_store=get_vector_store(),
            state_service=get_session_state_service(),
            bm25_index_service=get_bm25_index_service(),
            retrieval_cache_service=get_retrieval_cache_service(),
        )
        return cleanup_service.cleanup()
    finally:
        db.close()

async def cleanup_worker():
    while True:
        try:
            result = await asyncio.to_thread(
                _run_cleanup_cycle
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