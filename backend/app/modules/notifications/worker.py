"""Standalone notification outbox worker entry point."""

from datetime import UTC, datetime, timedelta
import logging
import time
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.modules.auth.models import AccountStatus, User, UserRole
from app.modules.notifications.models import NotificationStatus
from app.modules.notifications.repository import due_outbox, get_binding
from app.modules.notifications.wechat import WeChatClient, WeChatError

logger = logging.getLogger(__name__)

EVENT_TITLES = {
    "post_created": "有新的家庭近况",
    "qa_created": "有新的家庭问题",
    "qa_answered": "你的问题有新回复",
}


def format_notification_time(timezone_name: str, moment: datetime | None = None) -> str:
    current = (moment or datetime.now(UTC)).astimezone(ZoneInfo(timezone_name))
    return current.strftime("%Y年%m月%d日 %H:%M")


def _is_valid_recipient(recipient: object) -> bool:
    return (
        isinstance(recipient, User)
        and recipient.status == AccountStatus.ACTIVE
        and recipient.role in {UserRole.FAMILY, UserRole.OWNER}
    )


def process_once(db: Session, client: WeChatClient | None = None) -> int:
    settings = get_settings()
    if not settings.wechat_notifications_enabled:
        return 0
    client = client or WeChatClient()
    records = due_outbox(db, datetime.now(UTC))
    count = 0
    for record in records:
        if not _is_valid_recipient(record.recipient):
            record.status = NotificationStatus.FAILED
            record.last_error = "recipient is not an active family or owner user"
            db.commit()
            continue
        binding = get_binding(db, record.recipient_user_id)
        if binding is None:
            record.status = NotificationStatus.FAILED
            record.last_error = "recipient is not bound to WeChat"
            db.commit()
            continue
        try:
            summary = EVENT_TITLES.get(record.event_type, "家庭网站有新通知")
            happened_at = format_notification_time(settings.app_timezone)
            message_id = client.send_template(
                open_id=binding.open_id,
                summary=summary,
                happened_at=happened_at,
            )
            record.status = NotificationStatus.SENT
            record.sent_at = datetime.now(UTC)
            record.provider_message_id = message_id
            record.attempts += 1
        except (WeChatError, OSError) as error:
            record.attempts += 1
            record.last_error = str(error)[:500]
            if record.attempts >= settings.notification_max_attempts:
                record.status = NotificationStatus.FAILED
                logger.error(
                    "notification_delivery_failed_permanently outbox_id=%s event_type=%s aggregate_id=%s recipient_user_id=%s attempts=%s error=%s",
                    record.id,
                    record.event_type,
                    record.aggregate_id,
                    record.recipient_user_id,
                    record.attempts,
                    record.last_error,
                )
            else:
                record.next_attempt_at = datetime.now(UTC) + timedelta(seconds=min(3600, 2 ** record.attempts * 10))
        db.commit()
        count += 1
    return count


def main() -> None:
    settings = get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))
    while True:
        try:
            with SessionLocal() as db:
                process_once(db)
        except Exception:
            logger.exception("notification_worker_iteration_failed")
        time.sleep(settings.notification_worker_interval_seconds)


if __name__ == "__main__":
    main()
