"""Persistence helpers for notification records."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.auth.models import AccountStatus, User, UserRole
from app.modules.notifications.models import NotificationOutbox, NotificationStatus, WeChatBinding, WeChatBindingCode


def active_recipients(db: Session) -> list[User]:
    return list(db.scalars(select(User).where(User.status == AccountStatus.ACTIVE, User.role.in_([UserRole.FAMILY, UserRole.OWNER]))))


def get_binding(db: Session, user_id: UUID) -> WeChatBinding | None:
    return db.scalar(select(WeChatBinding).where(WeChatBinding.user_id == user_id))


def get_binding_by_open_id(db: Session, open_id: str) -> WeChatBinding | None:
    return db.scalar(select(WeChatBinding).where(WeChatBinding.open_id == open_id).options(joinedload(WeChatBinding.user)))


def get_binding_code(db: Session, code_hash: str) -> WeChatBindingCode | None:
    return db.scalar(select(WeChatBindingCode).where(WeChatBindingCode.code_hash == code_hash))


def due_outbox(db: Session, now: datetime, limit: int = 20) -> list[NotificationOutbox]:
    return list(db.scalars(
        select(NotificationOutbox)
        .where(NotificationOutbox.status == NotificationStatus.PENDING, NotificationOutbox.next_attempt_at <= now)
        .options(joinedload(NotificationOutbox.recipient))
        .order_by(NotificationOutbox.created_at)
        .with_for_update(skip_locked=True)
        .limit(limit)
    ))


def add_outbox(db: Session, *, event_type: str, aggregate_id: UUID, recipient_user_id: UUID) -> NotificationOutbox:
    record = NotificationOutbox(event_type=event_type, aggregate_id=aggregate_id, recipient_user_id=recipient_user_id)
    db.add(record)
    return record


def now_utc() -> datetime:
    return datetime.now(UTC)
