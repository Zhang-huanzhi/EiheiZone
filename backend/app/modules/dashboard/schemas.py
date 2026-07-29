"""Client-safe response schemas for the aggregated dashboard."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from app.modules.expenditures.schemas import ExpenditureResponse
from app.modules.posts.schemas import PostResponse
from app.modules.qas.schemas import QAResponse


ItemT = TypeVar("ItemT")


class DashboardSection(BaseModel, Generic[ItemT]):
    """A fixed-size dashboard summary with the full matching count."""

    items: list[ItemT]
    total: int = Field(ge=0)


class DashboardResponse(BaseModel):
    """Aggregate existing business responses without persisting new data."""

    posts: DashboardSection[PostResponse]
    qas: DashboardSection[QAResponse]
    expenditures: DashboardSection[ExpenditureResponse]
    unanswered_qas: DashboardSection[QAResponse]
