from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

from enum import StrEnum


class ExceptionCategory(StrEnum):
    """Stable, low-cardinality categories for request failures."""

    NONE = "none"
    HTTP = "http"
    VALIDATION = "validation"
    APP = "app"
    UNHANDLED = "unhandled"
    CANCELLED = "cancelled"


@dataclass
class RequestMetrics:
    """Aggregate database timings for one request context."""

    query_count: int = 0
    db_duration_ms: float = 0.0
    _started_queries: dict[int, float] = field(default_factory=dict)

    def start_query(self, execution_context: Any) -> None:
        self.query_count += 1
        self._started_queries[id(execution_context)] = perf_counter()

    def finish_query(self, execution_context: Any) -> None:
        started_at = self._started_queries.pop(id(execution_context), None)
        if started_at is not None:
            self.db_duration_ms += (perf_counter() - started_at) * 1000


_current_request_metrics: ContextVar[RequestMetrics | None] = ContextVar(
    "current_request_metrics",
    default=None,
)


def set_request_metrics(metrics: RequestMetrics) -> Token[RequestMetrics | None]:
    """Bind metrics to the current request execution context."""

    return _current_request_metrics.set(metrics)


def reset_request_metrics(token: Token[RequestMetrics | None]) -> None:
    """Restore the previous request metrics context."""

    _current_request_metrics.reset(token)


def get_request_metrics() -> RequestMetrics | None:
    """Return metrics for the current request, if one is active."""

    return _current_request_metrics.get()
