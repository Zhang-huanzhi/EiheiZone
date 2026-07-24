from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.auth.models import UserRole
from app.modules.auth.schemas import CurrentUserResponse, LoginRequest, LoginResponse


def test_login_request_accepts_credentials_without_normalizing_the_password() -> None:
    request = LoginRequest(login_name="family-a", password=" password with spaces ")

    assert request.login_name == "family-a"
    assert request.password == " password with spaces "


@pytest.mark.parametrize(
    "payload",
    [
        {"login_name": "", "password": "valid-password"},
        {"login_name": "family-a", "password": ""},
        {"login_name": "x" * 101, "password": "valid-password"},
        {"login_name": "family-a", "password": "x" * 1025},
    ],
)
def test_login_request_rejects_invalid_credential_shapes(payload: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        LoginRequest(**payload)


def test_login_response_exposes_only_client_safe_user_fields() -> None:
    response = LoginResponse(
        user=CurrentUserResponse(
            id=uuid4(),
            login_name="family-a",
            display_name="Family A",
            role=UserRole.FAMILY,
        ),
        csrf_token="csrf-token",
    )

    payload = response.model_dump(mode="json")

    assert payload["user"]["role"] == "family"
    assert set(payload["user"]) == {"id", "login_name", "display_name", "role"}
    assert "password_hash" not in payload
    assert "token_hash" not in payload
