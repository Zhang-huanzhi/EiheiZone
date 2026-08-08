"""Delete expired pending Post images and retry failed cleanups."""

from app.db.session import SessionLocal
from app.modules.posts.image_service import cleanup_orphan_images


def main() -> None:
    with SessionLocal() as db:
        deleted = cleanup_orphan_images(db)
    print(f"Deleted {deleted} orphan Post image(s).")


if __name__ == "__main__":
    main()
