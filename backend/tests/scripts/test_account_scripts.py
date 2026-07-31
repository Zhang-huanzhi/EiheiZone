from types import SimpleNamespace

import pytest

import scripts.create_user as create_user_script
import scripts.reset_password as reset_password_script
from app.core.errors import AppError
from app.modules.auth.models import UserRole


class DummySessionContext:
    def __enter__(self) -> object:
        return object()

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> bool:
        return False


@pytest.mark.parametrize(
    ("script", "arguments", "service_name", "result"),
    [
        (
            create_user_script,
            ["create_user.py", "--login-name", "family-a", "--display-name", "Family A", "--role", "family"],
            "create_user",
            SimpleNamespace(id="user-id", login_name="family-a", role=UserRole.FAMILY),
        ),
        (
            reset_password_script,
            ["reset_password.py", "--login-name", "family-a"],
            "reset_password",
            (SimpleNamespace(login_name="family-a"), 2),
        ),
    ],
)
def test_account_scripts_generate_password_only_after_success(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    script: object,
    arguments: list[str],
    service_name: str,
    result: object,
) -> None:
    monkeypatch.setattr(script, "SessionLocal", lambda: DummySessionContext())
    monkeypatch.setattr(script, service_name, lambda *_args, **_kwargs: result)
    monkeypatch.setattr(script.sys, "argv", arguments)
    monkeypatch.setattr(script.secrets, "token_urlsafe", lambda _size: "generated-test-password")

    assert script.main() == 0
    captured = capsys.readouterr()
    assert "generated-test-password" in captured.out
    assert captured.err == ""


@pytest.mark.parametrize(
    ("script", "arguments", "service_name", "message"),
    [
        (
            create_user_script,
            ["create_user.py", "--login-name", "family-a", "--display-name", "Family A", "--role", "family"],
            "create_user",
            "The login name is already in use",
        ),
        (
            reset_password_script,
            ["reset_password.py", "--login-name", "missing"],
            "reset_password",
            "User was not found",
        ),
    ],
)
def test_account_scripts_return_safe_failure_status(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    script: object,
    arguments: list[str],
    service_name: str,
    message: str,
) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        raise AppError(status_code=409, code="TEST_FAILURE", message=message)

    monkeypatch.setattr(script, "SessionLocal", lambda: DummySessionContext())
    monkeypatch.setattr(script, service_name, fail)
    monkeypatch.setattr(script.sys, "argv", arguments)
    monkeypatch.setattr(script.secrets, "token_urlsafe", lambda _size: "generated-test-password")

    assert script.main() == 1
    captured = capsys.readouterr()
    assert "generated-test-password" not in captured.out + captured.err
    assert "Traceback" not in captured.err
    assert message in captured.err


def test_create_user_script_prompts_for_missing_account_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: dict[str, object] = {}

    def create_user(*_args: object, **kwargs: object) -> SimpleNamespace:
        received.update(kwargs)
        return SimpleNamespace(id="user-id", login_name="family-a", role=UserRole.FAMILY)

    answers = iter(["family-a", "Family A", "family"])
    monkeypatch.setattr(create_user_script, "SessionLocal", lambda: DummySessionContext())
    monkeypatch.setattr(create_user_script, "create_user", create_user)
    monkeypatch.setattr(create_user_script.sys, "argv", ["create_user.py"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    monkeypatch.setattr(create_user_script.getpass, "getpass", lambda _prompt: "prompted-password")

    assert create_user_script.main() == 0
    assert received == {
        "login_name": "family-a",
        "display_name": "Family A",
        "role": UserRole.FAMILY,
        "plain_password": "prompted-password",
    }


def test_reset_password_script_prompts_for_missing_login_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: dict[str, object] = {}

    def reset_password(*_args: object, **kwargs: object) -> tuple[SimpleNamespace, int]:
        received.update(kwargs)
        return SimpleNamespace(login_name="family-a"), 0

    monkeypatch.setattr(reset_password_script, "SessionLocal", lambda: DummySessionContext())
    monkeypatch.setattr(reset_password_script, "reset_password", reset_password)
    monkeypatch.setattr(reset_password_script.sys, "argv", ["reset_password.py"])
    monkeypatch.setattr("builtins.input", lambda _prompt: "family-a")
    monkeypatch.setattr(reset_password_script.getpass, "getpass", lambda _prompt: "prompted-password")

    assert reset_password_script.main() == 0
    assert received == {
        "login_name": "family-a",
        "plain_password": "prompted-password",
    }
