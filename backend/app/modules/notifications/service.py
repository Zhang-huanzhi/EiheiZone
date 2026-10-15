"""Notification business rules and WeChat binding workflow."""

from datetime import UTC, datetime, timedelta
import hashlib
import secrets
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.auth.models import User
from app.modules.notifications.models import WeChatBinding, WeChatBindingCode
from app.modules.notifications.repository import (
    active_owners,
    active_recipients,
    add_outbox,
    get_active_recipient,
    get_binding,
    get_binding_by_open_id,
    get_binding_code,
)

CODE_TTL = timedelta(minutes=10)


def create_binding_code(db: Session, *, user: User) -> tuple[str, datetime]:
    raw = secrets.token_urlsafe(6).upper().replace("-", "").replace("_", "")[:8]
    expires_at = datetime.now(UTC) + CODE_TTL
    db.query(WeChatBindingCode).filter(WeChatBindingCode.user_id == user.id, WeChatBindingCode.used_at.is_(None)).update({WeChatBindingCode.used_at: datetime.now(UTC)})
    db.add(WeChatBindingCode(user_id=user.id, code_hash=_hash_code(raw), expires_at=expires_at))
    db.commit()
    return raw, expires_at


def binding_status(db: Session, *, user: User) -> dict[str, object]:
    binding = get_binding(db, user.id)
    return {"bound": binding is not None, "bound_at": binding.created_at if binding else None}


def unbind(db: Session, *, user: User) -> None:
    binding = get_binding(db, user.id)
    if binding:
        db.delete(binding)
        db.commit()


def bind_open_id_by_code(db: Session, *, open_id: str, raw_code: str) -> str:
    code = get_binding_code(db, _hash_code(raw_code.strip().upper()))
    now = datetime.now(UTC)
    if code is None or code.used_at is not None or code.expires_at <= now:
        raise AppError(status_code=400, code="INVALID_WECHAT_BINDING_CODE", message="Binding code is invalid or expired")
    existing = get_binding_by_open_id(db, open_id)
    if existing and existing.user_id != code.user_id:
        db.delete(existing)
        db.flush()
    current = get_binding(db, code.user_id)
    if current:
        current.open_id = open_id
        current.updated_at = now
    else:
        db.add(WeChatBinding(user_id=code.user_id, open_id=open_id))
    code.used_at = now
    db.commit()
    return "绑定成功，请返回网站查看通知设置。"


def enqueue_event(db: Session, *, event_type: str, aggregate_id: UUID, recipient_ids: list[UUID]) -> None:
    for recipient_id in dict.fromkeys(recipient_ids):
        add_outbox(db, event_type=event_type, aggregate_id=aggregate_id, recipient_user_id=recipient_id)


def enqueue_new_post(db: Session, *, post_id: UUID) -> None:
    enqueue_event(db, event_type="post_created", aggregate_id=post_id, recipient_ids=[user.id for user in active_recipients(db)])


def enqueue_new_question(db: Session, *, qa_id: UUID) -> None:
    enqueue_event(db, event_type="qa_created", aggregate_id=qa_id, recipient_ids=[owner.id for owner in active_owners(db)])


def enqueue_answer(db: Session, *, qa_id: UUID, asker_id: UUID) -> None:
    asker = get_active_recipient(db, asker_id)
    if asker is None:
        return
    enqueue_event(db, event_type="qa_answered", aggregate_id=qa_id, recipient_ids=[asker.id])


def _hash_code(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
