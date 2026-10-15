from datetime import UTC, datetime, timedelta
from hashlib import sha1
import hashlib
import logging
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

import app.core.security as security
import app.modules.auth.dependencies as auth_dependencies
import app.modules.auth.router as auth_router
import app.modules.notifications.router as notification_router
import app.modules.notifications.wechat as wechat_module
import app.modules.notifications.worker as worker_module
from app.core.errors import AppError
from app.modules.auth.models import AccountStatus, User, UserRole
from app.modules.auth.service import create_user
from app.modules.notifications.models import (
    NotificationOutbox,
    NotificationStatus,
    WeChatBinding,
    WeChatBindingCode,
)
from app.modules.notifications.service import (
    bind_open_id_by_code,
    binding_status,
    create_binding_code,
    enqueue_event,
    unbind,
)
from app.modules.notifications.wechat import (
    WeChatClient,
    WeChatError,
    parse_message,
    valid_signature,
    xml_reply,
)
from app.modules.notifications.worker import format_notification_time, process_once
from app.modules.posts.schemas import PostCreate
from app.modules.posts.service import create_post
from app.modules.qas.schemas import QAAnswerUpsert, QACreate
from app.modules.qas.service import create_question, upsert_answer


PASSWORD = "test-password-123"
ORIGIN = "http://localhost:3000"
WECHAT_TOKEN = "wechat-callback-secret"


def create_account(
    test_session: Session,
    role: UserRole,
    *,
    status: AccountStatus = AccountStatus.ACTIVE,
) -> User:
    user = create_user(
        test_session,
        login_name=f"notif-{role.value}-{uuid4().hex}",
        display_name=f"Notif {role.value.title()}",
        role=role,
        plain_password=PASSWORD,
    )
    if status != AccountStatus.ACTIVE:
        user.status = status
        test_session.commit()
    return user


def sign_callback(token: str, timestamp: str = "1700000000", nonce: str = "abc") -> dict[str, str]:
    signature = sha1("".join(sorted((token, timestamp, nonce))).encode()).hexdigest()
    return {"signature": signature, "timestamp": timestamp, "nonce": nonce}


def test_wechat_signature_uses_sorted_token_parts() -> None:
    token, timestamp, nonce = "secret", "1700000000", "abc"
    signature = sha1("".join(sorted((token, timestamp, nonce))).encode()).hexdigest()
    assert valid_signature(token=token, timestamp=timestamp, nonce=nonce, signature=signature)
    assert not valid_signature(token=token, timestamp=timestamp, nonce=nonce, signature="bad")


def test_wechat_xml_message_round_trip_and_invalid_xml_rejection() -> None:
    body = xml_reply(open_id="user", account_id="account", content="绑定成功")
    parsed = parse_message(body.encode())
    assert parsed["FromUserName"] == "account"
    assert parsed["ToUserName"] == "user"
    assert parsed["Content"] == "绑定成功"
    assert int(parsed["CreateTime"]) > 0

    with pytest.raises(AppError) as error:
        parse_message(b"<xml><unclosed>")
    assert error.value.status_code == 400
    assert error.value.code == "WECHAT_XML_INVALID"


def test_invalid_binding_code_error_contract() -> None:
    error = AppError(status_code=400, code="INVALID_WECHAT_BINDING_CODE", message="invalid")
    assert error.status_code == 400
    assert error.code == "INVALID_WECHAT_BINDING_CODE"


def test_wechat_client_caches_token_omits_url_and_clears_token_on_send_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = SimpleNamespace(
        wechat_app_id="wx-test-app",
        wechat_app_secret="wx-test-secret",
        wechat_template_id="tpl-123",
    )
    monkeypatch.setattr(wechat_module, "get_settings", lambda: settings)

    calls: list[tuple[str, dict[str, Any] | None]] = []
    responses: list[dict[str, Any]] = [
        {"access_token": "token-1", "expires_in": 7200},
        {"errcode": 0, "msgid": 987654},
        {"errcode": 40001, "errmsg": "invalid credential"},
        {"access_token": "token-2", "expires_in": 7200},
        {"errcode": 0, "msgid": 987655},
    ]

    def fake_request_json(url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        calls.append((url, payload))
        return responses.pop(0)

    monkeypatch.setattr(WeChatClient, "_request_json", staticmethod(fake_request_json))
    wechat_client = WeChatClient()

    message_id = wechat_client.send_template(
        open_id="openid-mom",
        summary="有新的家庭近况",
        happened_at="2026年10月15日 19:46",
    )
    assert message_id == "987654"
    assert len(calls) == 2
    sent_payload = calls[1][1]
    assert sent_payload is not None
    assert "url" not in sent_payload
    assert sent_payload["touser"] == "openid-mom"
    assert sent_payload["template_id"] == "tpl-123"
    assert sent_payload["data"] == {
        "keyword1": {"value": "有新的家庭近况"},
        "keyword2": {"value": "2026年10月15日 19:46"},
    }

    with pytest.raises(WeChatError, match="invalid credential"):
        wechat_client.send_template(
            open_id="openid-mom",
            summary="有新的家庭问题",
            happened_at="2026年10月15日 19:46",
        )

    second_id = wechat_client.send_template(
        open_id="openid-mom",
        summary="有新的家庭问题",
        happened_at="2026年10月15日 19:46",
    )
    assert second_id == "987655"
    assert len(calls) == 5


def test_notification_time_uses_shanghai_clock() -> None:
    moment = datetime(2026, 10, 15, 11, 46, tzinfo=UTC)
    assert format_notification_time("Asia/Shanghai", moment) == "2026年10月15日 19:46"


def test_binding_code_lifecycle_and_openid_binding(test_session: Session) -> None:
    family_a = create_account(test_session, UserRole.FAMILY)
    family_b = create_account(test_session, UserRole.FAMILY)

    first_code, _ = create_binding_code(test_session, user=family_a)
    second_code, expires_at = create_binding_code(test_session, user=family_a)
    assert expires_at > datetime.now(UTC)

    stored_codes = list(
        test_session.scalars(
            select(WeChatBindingCode).where(WeChatBindingCode.user_id == family_a.id)
        )
    )
    assert all(record.code_hash != second_code for record in stored_codes)
    assert any(
        record.code_hash == hashlib.sha256(second_code.encode("utf-8")).hexdigest()
        and record.used_at is None
        for record in stored_codes
    )

    with pytest.raises(AppError) as replaced_error:
        bind_open_id_by_code(test_session, open_id="openid-1", raw_code=first_code)
    assert replaced_error.value.code == "INVALID_WECHAT_BINDING_CODE"

    reply = bind_open_id_by_code(test_session, open_id="openid-1", raw_code=f" {second_code.lower()} ")
    assert "绑定成功" in reply
    assert binding_status(test_session, user=family_a)["bound"] is True

    with pytest.raises(AppError) as reuse_error:
        bind_open_id_by_code(test_session, open_id="openid-2", raw_code=second_code)
    assert reuse_error.value.code == "INVALID_WECHAT_BINDING_CODE"

    transfer_code, _ = create_binding_code(test_session, user=family_b)
    bind_open_id_by_code(test_session, open_id="openid-1", raw_code=transfer_code)
    assert binding_status(test_session, user=family_a)["bound"] is False
    assert binding_status(test_session, user=family_b)["bound"] is True

    unbind(test_session, user=family_b)
    assert binding_status(test_session, user=family_b)["bound"] is False


def test_expired_binding_code_is_rejected(test_session: Session) -> None:
    family = create_account(test_session, UserRole.FAMILY)
    raw_code, _ = create_binding_code(test_session, user=family)
    code_record = test_session.scalar(
        select(WeChatBindingCode).where(WeChatBindingCode.user_id == family.id)
    )
    assert code_record is not None
    code_record.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    test_session.commit()

    with pytest.raises(AppError) as expired_error:
        bind_open_id_by_code(test_session, open_id="openid-expired", raw_code=raw_code)
    assert expired_error.value.code == "INVALID_WECHAT_BINDING_CODE"


def test_qa_and_post_outbox_recipient_rules_and_idempotency(test_session: Session) -> None:
    owner = create_account(test_session, UserRole.OWNER)
    family_asker = create_account(test_session, UserRole.FAMILY)
    family_other = create_account(test_session, UserRole.FAMILY)
    disabled_family = create_account(
        test_session, UserRole.FAMILY, status=AccountStatus.INACTIVE
    )

    post = create_post(
        test_session,
        user=family_asker,
        payload=PostCreate(title="New family post", body="Post content"),
    )
    post_outbox = list(
        test_session.scalars(
            select(NotificationOutbox).where(
                NotificationOutbox.event_type == "post_created",
                NotificationOutbox.aggregate_id == post.id,
            )
        )
    )
    assert {record.recipient_user_id for record in post_outbox} == {
        owner.id,
        family_asker.id,
        family_other.id,
    }
    assert disabled_family.id not in {record.recipient_user_id for record in post_outbox}

    enqueue_event(
        test_session,
        event_type="post_created",
        aggregate_id=post.id,
        recipient_ids=[owner.id, family_asker.id],
    )
    test_session.commit()
    deduped_outbox = list(
        test_session.scalars(
            select(NotificationOutbox).where(
                NotificationOutbox.event_type == "post_created",
                NotificationOutbox.aggregate_id == post.id,
            )
        )
    )
    assert len(deduped_outbox) == 3

    qa = create_question(
        test_session,
        user=family_asker,
        payload=QACreate(question="When is the next visit?"),
    )
    qa_created_outbox = list(
        test_session.scalars(
            select(NotificationOutbox).where(
                NotificationOutbox.event_type == "qa_created",
                NotificationOutbox.aggregate_id == qa.id,
            )
        )
    )
    assert [record.recipient_user_id for record in qa_created_outbox] == [owner.id]

    upsert_answer(
        test_session,
        user=owner,
        qa_id=qa.id,
        payload=QAAnswerUpsert(answer="Next weekend"),
    )
    upsert_answer(
        test_session,
        user=owner,
        qa_id=qa.id,
        payload=QAAnswerUpsert(answer="Updated to Sunday"),
    )
    qa_answered_outbox = list(
        test_session.scalars(
            select(NotificationOutbox).where(
                NotificationOutbox.event_type == "qa_answered",
                NotificationOutbox.aggregate_id == qa.id,
            )
        )
    )
    assert [record.recipient_user_id for record in qa_answered_outbox] == [family_asker.id]


def test_worker_processes_delivery_retries_and_logs_permanent_failure(
    test_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    bound_user = create_account(test_session, UserRole.FAMILY)
    unbound_user = create_account(test_session, UserRole.FAMILY)
    disabled_user = create_account(
        test_session, UserRole.FAMILY, status=AccountStatus.INACTIVE
    )
    test_session.add(WeChatBinding(user_id=bound_user.id, open_id="openid-bound"))
    test_session.add(WeChatBinding(user_id=disabled_user.id, open_id="openid-disabled"))

    aggregate_ok = uuid4()
    aggregate_fail = uuid4()
    enqueue_event(
        test_session,
        event_type="post_created",
        aggregate_id=aggregate_ok,
        recipient_ids=[bound_user.id, unbound_user.id, disabled_user.id],
    )
    enqueue_event(
        test_session,
        event_type="qa_answered",
        aggregate_id=aggregate_fail,
        recipient_ids=[bound_user.id],
    )
    test_session.commit()

    disabled_settings = SimpleNamespace(
        wechat_notifications_enabled=False,
        notification_max_attempts=2,
        app_timezone="Asia/Shanghai",
    )
    monkeypatch.setattr(worker_module, "get_settings", lambda: disabled_settings)
    assert process_once(test_session) == 0

    enabled_settings = SimpleNamespace(
        wechat_notifications_enabled=True,
        notification_max_attempts=2,
        app_timezone="Asia/Shanghai",
    )
    monkeypatch.setattr(worker_module, "get_settings", lambda: enabled_settings)

    class StubWeChatClient:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str]] = []

        def send_template(self, *, open_id: str, summary: str, happened_at: str) -> str:
            self.calls.append((open_id, summary))
            if summary == "你的问题有新回复":
                raise WeChatError("simulated WeChat upstream timeout")
            return "msg-success-1"

    stub_client = StubWeChatClient()
    processed = process_once(test_session, client=stub_client)  # type: ignore[arg-type]
    assert processed == 2

    records = {
        (row.aggregate_id, row.recipient_user_id): row
        for row in test_session.scalars(select(NotificationOutbox))
    }
    sent_record = records[(aggregate_ok, bound_user.id)]
    assert sent_record.status == NotificationStatus.SENT
    assert sent_record.provider_message_id == "msg-success-1"
    assert sent_record.sent_at is not None
    assert sent_record.attempts == 1

    unbound_record = records[(aggregate_ok, unbound_user.id)]
    assert unbound_record.status == NotificationStatus.FAILED
    assert unbound_record.last_error == "recipient is not bound to WeChat"

    disabled_record = records[(aggregate_ok, disabled_user.id)]
    assert disabled_record.status == NotificationStatus.FAILED
    assert disabled_record.last_error == "recipient is not an active family or owner user"

    retrying_record = records[(aggregate_fail, bound_user.id)]
    assert retrying_record.status == NotificationStatus.PENDING
    assert retrying_record.attempts == 1
    assert retrying_record.next_attempt_at > datetime.now(UTC)

    retrying_record.next_attempt_at = datetime.now(UTC) - timedelta(seconds=1)
    test_session.commit()

    worker_module.logger.disabled = False
    with caplog.at_level(logging.ERROR, logger=worker_module.logger.name):
        process_once(test_session, client=stub_client)  # type: ignore[arg-type]

    assert retrying_record.status == NotificationStatus.FAILED
    assert retrying_record.attempts == 2
    assert "notification_delivery_failed_permanently" in caplog.text


def test_wechat_callback_and_notification_settings_api(
    client: TestClient,
    test_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = SimpleNamespace(
        app_origin=ORIGIN,
        csrf_secret="test-csrf-secret-with-at-least-thirty-two-characters",
        csrf_token_ttl_seconds=3600,
        session_cookie_name="pfp_session",
        csrf_cookie_name="pfp_csrf",
        cookie_secure=False,
        session_ttl_days=30,
        wechat_token=WECHAT_TOKEN,
    )
    monkeypatch.setattr(security, "get_settings", lambda: settings)
    monkeypatch.setattr(auth_dependencies, "get_settings", lambda: settings)
    monkeypatch.setattr(auth_router, "get_settings", lambda: settings)
    monkeypatch.setattr(notification_router, "get_settings", lambda: settings)

    family = create_account(test_session, UserRole.FAMILY)
    csrf_token = client.get("/api/v1/auth/csrf").json()["csrf_token"]
    login_res = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
        json={"login_name": family.login_name, "password": PASSWORD},
    )
    assert login_res.status_code == 200
    csrf_token = login_res.json()["csrf_token"]

    initial_status = client.get("/api/v1/notifications/wechat")
    assert initial_status.status_code == 200
    assert initial_status.json() == {"bound": False, "bound_at": None}

    code_res = client.post(
        "/api/v1/notifications/wechat/code",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
    )
    assert code_res.status_code == 200
    binding_code = code_res.json()["code"]

    bad_verify = client.get(
        "/api/v1/wechat/callback",
        params={"signature": "bad", "timestamp": "1", "nonce": "2", "echostr": "hello"},
    )
    assert bad_verify.status_code == 403

    good_verify = client.get(
        "/api/v1/wechat/callback",
        params={**sign_callback(WECHAT_TOKEN), "echostr": "echo-ok-123"},
    )
    assert good_verify.status_code == 200
    assert good_verify.text == "echo-ok-123"

    subscribe_xml = (
        "<xml><ToUserName><![CDATA[gh_test]]></ToUserName>"
        "<FromUserName><![CDATA[openid-parent]]></FromUserName>"
        "<MsgType><![CDATA[event]]></MsgType>"
        "<Event><![CDATA[subscribe]]></Event></xml>"
    )
    subscribe_res = client.post(
        "/api/v1/wechat/callback",
        params=sign_callback(WECHAT_TOKEN),
        content=subscribe_xml.encode("utf-8"),
    )
    assert subscribe_res.status_code == 200
    assert "欢迎关注" in subscribe_res.text

    bind_xml = (
        "<xml><ToUserName><![CDATA[gh_test]]></ToUserName>"
        "<FromUserName><![CDATA[openid-parent]]></FromUserName>"
        "<MsgType><![CDATA[text]]></MsgType>"
        f"<Content><![CDATA[{binding_code}]]></Content></xml>"
    )
    bind_res = client.post(
        "/api/v1/wechat/callback",
        params=sign_callback(WECHAT_TOKEN),
        content=bind_xml.encode("utf-8"),
    )
    assert bind_res.status_code == 200
    assert "绑定成功" in bind_res.text

    bound_status = client.get("/api/v1/notifications/wechat")
    assert bound_status.status_code == 200
    assert bound_status.json()["bound"] is True
    assert bound_status.json()["bound_at"] is not None

    invalid_bind_res = client.post(
        "/api/v1/wechat/callback",
        params=sign_callback(WECHAT_TOKEN),
        content=bind_xml.encode("utf-8"),
    )
    assert invalid_bind_res.status_code == 200
    assert "绑定码无效或已过期" in invalid_bind_res.text

    unbind_res = client.delete(
        "/api/v1/notifications/wechat",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
    )
    assert unbind_res.status_code == 204
    assert client.get("/api/v1/notifications/wechat").json()["bound"] is False
