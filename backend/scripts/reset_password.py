"""Reset one account password and invalidate every old login session."""

import argparse
import getpass
import secrets
import sys
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError


BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIRECTORY))

from app.db.session import SessionLocal  # noqa: E402
from app.core.errors import AppError  # noqa: E402
from app.modules.auth.service import (  # noqa: E402
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    reset_password,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--login-name")
    parser.add_argument("--prompt-password", action="store_true")
    args = parser.parse_args()

    print("Reset an account password. Press Enter after every answer.")
    interactive = args.login_name is None
    login_name = args.login_name or input("Login name: ").strip()
    generated_password = not (args.prompt_password or interactive)
    if generated_password:
        password = secrets.token_urlsafe(24)
        print("A random password will be generated and shown once after success.")
    else:
        password = _prompt_password()
    try:
        with SessionLocal() as db:
            user, deleted_count = reset_password(db, login_name=login_name, plain_password=password)
    except AppError as error:
        print(f"Password reset failed: {error.message}", file=sys.stderr)
        return 1
    except SQLAlchemyError:
        print("Password reset failed due to a database error.", file=sys.stderr)
        return 1
    except Exception:
        print("Password reset failed unexpectedly.", file=sys.stderr)
        return 1

    print(f"Reset password for {user.login_name}; invalidated {deleted_count} sessions")
    if generated_password:
        print(f"New password (show once): {password}")
    return 0


def _prompt_password() -> str:
    print(
        f"Enter the new password now, then press Enter. "
        f"It must contain {MIN_PASSWORD_LENGTH} to {MAX_PASSWORD_LENGTH} characters."
    )
    print(
        "Password input should be hidden. If this IDE Run window displays characters, "
        "stop and use the IDE Terminal before entering a real password."
    )
    while True:
        password = getpass.getpass("New password: ")
        confirmation = getpass.getpass("Confirm new password: ")
        if password != confirmation:
            print("Passwords did not match. Please try again.", file=sys.stderr)
            continue
        if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
            print(
                f"Password must contain {MIN_PASSWORD_LENGTH} to {MAX_PASSWORD_LENGTH} characters. "
                "Please try again.",
                file=sys.stderr,
            )
            continue
        return password


if __name__ == "__main__":
    raise SystemExit(main())
