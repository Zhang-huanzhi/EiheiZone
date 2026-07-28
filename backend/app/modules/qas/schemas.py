"""Client-safe input and output schemas for QA endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.modules.qas.models import QAStatus


MAX_QUESTION_LENGTH = 2000
MAX_ANSWER_LENGTH = 10000


def _validate_text(value: str, *, label: str, maximum: int) -> str:
    if not value.strip():
        raise ValueError(f"{label} must not be blank")
    if len(value) > maximum:
        raise ValueError(f"{label} must contain at most {maximum} characters")
    return value


class QACreate(BaseModel):
    """Accept the question text a Family user may submit."""

    question: str

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        return _validate_text(value, label="Question", maximum=MAX_QUESTION_LENGTH)


class QAAnswerUpsert(BaseModel):
    """Accept the complete current answer an Owner may save."""

    answer: str

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, value: str) -> str:
        return _validate_text(value, label="Answer", maximum=MAX_ANSWER_LENGTH)


class QAResponse(BaseModel):
    """Return the QA and only the actor information pages need."""

    id: UUID
    asked_by: UUID
    asked_by_display_name: str = Field(min_length=1, max_length=80)
    question: str = Field(min_length=1, max_length=MAX_QUESTION_LENGTH)
    answer: str | None = Field(default=None, min_length=1, max_length=MAX_ANSWER_LENGTH)
    answered_by: UUID | None
    answered_by_display_name: str | None = Field(default=None, min_length=1, max_length=80)
    status: QAStatus
    answered_at: datetime | None
    created_at: datetime
    updated_at: datetime
