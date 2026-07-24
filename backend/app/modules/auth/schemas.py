"""Client-safe request and response schemas for authentication endpoints."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.auth.models import UserRole


class CsrfResponse(BaseModel):
    """Return the CSRF token paired with the readable CSRF cookie."""

    csrf_token: str = Field(min_length=1)


class LoginRequest(BaseModel):
    """Accept the credentials required to start a server-side session."""

    login_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=1024)


class CurrentUserResponse(BaseModel):
    """Expose only the user information required by pages and role checks."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    login_name: str
    display_name: str
    role: UserRole


class LoginResponse(BaseModel):
    """Return the authenticated user and the rotated CSRF token after login."""

    user: CurrentUserResponse
    csrf_token: str = Field(min_length=1)
