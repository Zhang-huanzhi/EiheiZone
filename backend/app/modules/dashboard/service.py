"""Read-only orchestration across the Post, QA, and Expenditure services."""

from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams
from app.modules.auth.models import User
from app.modules.dashboard.schemas import DashboardResponse, DashboardSection
from app.modules.expenditures.service import list_expenditures_for_user
from app.modules.posts.service import list_posts_for_user
from app.modules.qas.service import (
    list_qas_for_user,
    list_unanswered_qas_for_user,
)


DASHBOARD_ITEM_LIMIT = 5


def get_dashboard(db: Session, *, user: User) -> DashboardResponse:
    """Return fixed-size summaries while preserving each module's permissions."""

    pagination = PaginationParams(offset=0, limit=DASHBOARD_ITEM_LIMIT)
    posts = list_posts_for_user(db, user=user, pagination=pagination)
    qas = list_qas_for_user(db, user=user, pagination=pagination)
    expenditures = list_expenditures_for_user(
        db,
        user=user,
        pagination=pagination,
    )
    unanswered_qas = list_unanswered_qas_for_user(
        db,
        user=user,
        pagination=pagination,
    )

    return DashboardResponse(
        posts=DashboardSection(items=posts.items, total=posts.total),
        qas=DashboardSection(items=qas.items, total=qas.total),
        expenditures=DashboardSection(
            items=expenditures.items,
            total=expenditures.total,
        ),
        unanswered_qas=DashboardSection(
            items=unanswered_qas.items,
            total=unanswered_qas.total,
        ),
    )
