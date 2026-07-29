"""HTTP endpoint for authenticated dashboard aggregation."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import CurrentUser, require_family_access
from app.modules.dashboard.schemas import DashboardResponse
from app.modules.dashboard.service import get_dashboard


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def read_dashboard(
    current_user: CurrentUser = Depends(require_family_access),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    """Return summaries for the current authenticated family reader."""

    return get_dashboard(db, user=current_user.user)
