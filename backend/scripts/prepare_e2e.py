"""Create synthetic browser-test accounts in the protected test database."""

import os
import sys
from pathlib import Path

from sqlalchemy.engine import make_url


BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIRECTORY))

from app.core.config import get_settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.modules.auth.models import UserRole  # noqa: E402
from app.modules.auth.service import create_user  # noqa: E402


TEST_DATABASE_NAME = "eiheizone_test"


def main() -> None:
    settings = get_settings()
    if make_url(settings.database_url).database != TEST_DATABASE_NAME:
        raise RuntimeError(f"E2E account setup must target {TEST_DATABASE_NAME}")

    with SessionLocal() as db:
        create_user(
            db,
            login_name=required_environment("E2E_FAMILY_LOGIN_NAME"),
            display_name="E2E Family",
            role=UserRole.FAMILY,
            plain_password=required_environment("E2E_FAMILY_PASSWORD"),
        )
        create_user(
            db,
            login_name=required_environment("E2E_OWNER_LOGIN_NAME"),
            display_name="E2E Owner",
            role=UserRole.OWNER,
            plain_password=required_environment("E2E_OWNER_PASSWORD"),
        )


def required_environment(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


if __name__ == "__main__":
    main()
