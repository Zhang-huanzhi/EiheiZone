from typing import Annotated, Generic, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel, Field


ItemT = TypeVar("ItemT")


class PaginationParams(BaseModel):
    """Validated pagination input shared by all future list endpoints."""

    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


def get_pagination(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginationParams:
    """Read and validate the common offset and limit query parameters."""

    return PaginationParams(offset=offset, limit=limit)


Pagination = Annotated[PaginationParams, Depends(get_pagination)]


class Page(BaseModel, Generic[ItemT]):
    """A stable response shape for every future paginated endpoint."""

    items: list[ItemT]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
