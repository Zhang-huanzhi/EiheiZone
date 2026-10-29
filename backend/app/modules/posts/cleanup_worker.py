"""Standalone media cleanup worker entry point."""

import logging
import time

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.modules.posts.image_service import run_media_cleanup

logger = logging.getLogger(__name__)


def process_once() -> None:
    settings = get_settings()
    with SessionLocal() as db:
        run_media_cleanup(
            db,
            scan_orphans=True,
            max_items=settings.media_cleanup_max_items,
        )


def main() -> None:
    settings = get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))
    while True:
        try:
            process_once()
        except Exception:
            logger.exception("media_cleanup_worker_iteration_failed")
        time.sleep(settings.media_cleanup_worker_interval_seconds)


if __name__ == "__main__":
    main()
