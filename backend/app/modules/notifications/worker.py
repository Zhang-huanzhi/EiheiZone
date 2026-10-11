"""Standalone notification outbox worker entry point."""

from datetime import UTC, datetime, timedelta
import logging
import time

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.modules.notifications.models import NotificationStatus
from app.modules.notifications.repository import due_outbox, get_binding
from app.modules.notifications.wechat import WeChatClient, WeChatError

logger = logging.getLogger(__name__)


def process_once(db: Session, client: WeChatClient | None = None) -> int:
    settings = get_settings()
    if not settings.wechat_notifications_enabled:
        return 0
    client = client or WeChatClient()
    records = due_outbox(db, datetime.now(UTC))
    count = 0
    for record in records:
        binding = get_binding(db, record.recipient_user_id)
        if binding is None:
            record.status = NotificationStatus.FAILED
            record.last_error = "recipient is not bound to WeChat"
            db.commit()
            continue
        try:
            title = {"post_created": "有新的家庭近况", "qa_created": "有新的家庭问题", "qa_answered": "你的问题有新回复"}.get(record.event_type, "家庭网站有新通知")
            message_id = client.send_template(open_id=binding.open_id, title=title, url=settings.wechat_message_url)
            record.status = NotificationStatus.SENT
            record.sent_at = datetime.now(UTC)
            record.provider_message_id = message_id
            record.attempts += 1
        except (WeChatError, OSError) as error:
            record.attempts += 1
            record.last_error = str(error)[:500]
            if record.attempts >= settings.notification_max_attempts:
                record.status = NotificationStatus.FAILED
            else:
                record.next_attempt_at = datetime.now(UTC) + timedelta(seconds=min(3600, 2 ** record.attempts * 10))
        db.commit()
        count += 1
    return count


def main() -> None:
    settings = get_settings()
    while True:
        with SessionLocal() as db:
            process_once(db)
        time.sleep(settings.notification_worker_interval_seconds)


if __name__ == "__main__":
    main()
