from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.request_id import REQUEST_ID_HEADER


class FieldError(BaseModel):
    """Describe one invalid API input field."""

    field: str
    message: str
    type: str


class ErrorDetail(BaseModel):
    """Describe a client-safe API error."""

    code: str
    message: str
    field_errors: list[FieldError] = Field(default_factory=list)
    request_id: str


class ErrorResponse(BaseModel):
    """Wrap all API errors in one stable response shape."""

    error: ErrorDetail


class AppError(Exception):
    """Represent an expected application error before it becomes an HTTP response."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        field_errors: list[FieldError] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.field_errors = list(field_errors or [])


HTTP_ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    429: "RATE_LIMITED",
}

HTTP_ERROR_MESSAGES = {
    400: "The request is invalid",
    401: "Authentication is required",
    403: "You do not have permission to perform this action",
    404: "The requested resource was not found",
    409: "The request conflicts with the current resource state",
    429: "Too many requests",
}


def get_request_id(request: Request) -> str:
    """Return the middleware ID, with a fallback for independently tested handlers."""

    request_id = getattr(request.state, "request_id", None)
    if isinstance(request_id, str):
        return request_id
    return str(uuid4())


def error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    field_errors: list[FieldError] | None = None,
) -> JSONResponse:
    """Build an API error response without exposing internal exception details."""

    request_id = get_request_id(request)
    content = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            field_errors=field_errors or [],
            request_id=request_id,
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=content.model_dump(mode="json"),
        headers={REQUEST_ID_HEADER: request_id},
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Convert expected application errors into the shared API error shape."""

    return error_response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        field_errors=exc.field_errors,
    )


async def request_validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Convert FastAPI query, path, and body validation errors into field errors."""

    field_errors = [
        FieldError(
            field=".".join(str(part) for part in error["loc"]),
            message=str(error["msg"]),
            type=str(error["type"]),
        )
        for error in exc.errors()
    ]
    return error_response(
        request,
        status_code=422,
        code="VALIDATION_ERROR",
        message="Request fields are invalid",
        field_errors=field_errors,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Convert framework HTTP errors, including missing routes, into API errors."""

    return error_response(
        request,
        status_code=exc.status_code,
        code=HTTP_ERROR_CODES.get(exc.status_code, "HTTP_ERROR"),
        message=HTTP_ERROR_MESSAGES.get(exc.status_code, "The request could not be completed"),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a safe response for unexpected failures; middleware logs the exception."""

    return error_response(
        request,
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register the application's one shared set of API error handlers."""

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
