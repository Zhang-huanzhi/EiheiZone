"""Inspect or clean stale Post images and unreferenced media files."""

import argparse
import json
from datetime import timedelta

from app.db.session import SessionLocal
from app.core.config import get_settings
from app.modules.posts.image_service import cleanup_orphan_images


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--scan-orphans", action="store_true")
    parser.add_argument("--max-items", type=int, default=None)
    args = parser.parse_args()
    with SessionLocal() as db:
        stats = cleanup_orphan_images(
            db,
            dry_run=args.dry_run,
            scan_orphans=args.scan_orphans,
            max_items=args.max_items,
            grace_period=timedelta(hours=get_settings().media_cleanup_orphan_grace_hours),
        )
    print(json.dumps(stats.as_dict(), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
