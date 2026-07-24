"""Create one Family or Owner account from a trusted server terminal."""

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
from app.modules.auth.models import UserRole  # noqa: E402
from app.modules.auth.service import (  # noqa: E402
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    create_user,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--login-name")
    parser.add_argument("--display-name")
    parser.add_argument("--role", choices=[role.value for role in UserRole])
    parser.add_argument("--prompt-password", action="store_true")
    args = parser.parse_args()

    print("Create a Family or Owner account. Press Enter after every answer.")

    interactive = any(
        value is None
        for value in (args.login_name, args.display_name, args.role)
    )
    login_name = args.login_name or input("Login name: ").strip()
    display_name = args.display_name or input("Display name: ").strip()
    role = args.role or _prompt_role()
    generated_password = not (args.prompt_password or interactive)
    if generated_password:
        password = secrets.token_urlsafe(24)
        print("A random initial password will be generated and shown once after success.")
    else:
        password = _prompt_password("initial")
    try:
        with SessionLocal() as db:
            user = create_user(
                db,
                login_name=login_name,
                display_name=display_name,
                role=UserRole(role),
                plain_password=password,
            )
    except AppError as error:
        print(f"Account creation failed: {error.message}", file=sys.stderr)
        return 1
    except SQLAlchemyError:
        print("Account creation failed due to a database error.", file=sys.stderr)
        return 1
    except Exception:
        print("Account creation failed unexpectedly.", file=sys.stderr)
        return 1

    print(f"Created {user.role.value} account {user.login_name} ({user.id})")
    if generated_password:
        print(f"Initial password (show once): {password}")
    return 0


def _prompt_role() -> str:
    allowed_roles = ", ".join(role.value for role in UserRole)
    while True:
        role = input(f"Role ({allowed_roles}): ").strip().lower()
        if role in {member.value for member in UserRole}:
            return role
        print(f"Role must be one of: {allowed_roles}.", file=sys.stderr)


def _prompt_password(label: str) -> str:
    print(
        f"Enter the {label} password now, then press Enter. "
        f"It must contain {MIN_PASSWORD_LENGTH} to {MAX_PASSWORD_LENGTH} characters."
    )
    print(
        "Password input should be hidden. If this IDE Run window displays characters, "
        "stop and use the IDE Terminal before entering a real password."
    )
    while True:
        password = getpass.getpass(f"{label.capitalize()} password: ")
        confirmation = getpass.getpass(f"Confirm {label} password: ")
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
