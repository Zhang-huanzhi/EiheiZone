import asyncio
import logging
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from app.core.config import get_settings
from app.core.request_metrics import (
    ExceptionCategory,
    RequestMetrics,
    reset_request_metrics,
    set_request_metrics,
)


REQUEST_ID_HEADER = "X-Request-ID"
logger = logging.getLogger(__name__)


def get_slow_request_threshold_ms() -> int:
    """Return the configured threshold for emitting slow request warnings."""

    return get_settings().slow_request_threshold_ms


async def request_id_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """Assign a request ID and return it with every normal response."""

    request_id = str(uuid4())
    request.state.request_id = request_id
    request.state.exception_category = ExceptionCategory.NONE.value
    started_at = perf_counter()
    metrics = RequestMetrics()
    metrics_token = set_request_metrics(metrics)
    response: Response | None = None
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
    except asyncio.CancelledError:
        request.state.exception_category = ExceptionCategory.CANCELLED.value
        status_code = 499
        raise
    except Exception:
        request.state.exception_category = ExceptionCategory.UNHANDLED.value
        logger.exception("Unhandled request error", extra={"request_id": request_id})
        raise
    finally:
        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        exception_category = getattr(
            request.state,
            "exception_category",
            ExceptionCategory.NONE.value,
        )
        log_fields = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "exception_category": exception_category,
        }
        logger.info("Request completed", extra=log_fields)

        if duration_ms >= get_slow_request_threshold_ms():
            logger.warning(
                "Slow request",
                extra={
                    **log_fields,
                    "db_query_count": metrics.query_count,
                    "db_duration_ms": round(metrics.db_duration_ms, 2),
                },
            )

        if response is not None:
            response.headers[REQUEST_ID_HEADER] = request_id
        reset_request_metrics(metrics_token)

    if response is None:
        raise RuntimeError("Request middleware completed without a response")
    return response
