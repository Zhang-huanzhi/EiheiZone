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
    """Accept the question text and optional proxy flag a Family or Owner user may submit."""

    question: str
    is_proxy: bool = False

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        return _validate_text(value, label="Question", maximum=MAX_QUESTION_LENGTH)


class QAAnswerUpsert(BaseModel):
    """Accept the answer text for backward compatibility."""

    answer: str
    is_proxy: bool = False

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, value: str) -> str:
        return _validate_text(value, label="Answer", maximum=MAX_ANSWER_LENGTH)


class QAAnswerCreate(BaseModel):
    """Accept the answer content and proxy flag for a new answer."""

    content: str
    is_proxy: bool = False

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        return _validate_text(value, label="Answer", maximum=MAX_ANSWER_LENGTH)


class QAAnswerUpdate(BaseModel):
    """Accept updated answer content and proxy flag."""

    content: str
    is_proxy: bool = False

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        return _validate_text(value, label="Answer", maximum=MAX_ANSWER_LENGTH)


class QAAnswerResponse(BaseModel):
    """Return an individual answer and author display information."""

    id: UUID
    qa_id: UUID
    author_id: UUID
    author_display_name: str = Field(min_length=1, max_length=80)
    content: str = Field(min_length=1, max_length=MAX_ANSWER_LENGTH)
    is_proxy: bool = False
    created_at: datetime
    updated_at: datetime


class QAResponse(BaseModel):
    """Return the QA thread and its answers."""

    id: UUID
    asked_by: UUID
    asked_by_display_name: str = Field(min_length=1, max_length=80)
    question: str = Field(min_length=1, max_length=MAX_QUESTION_LENGTH)
    is_proxy: bool = False
    status: QAStatus
    answers_count: int = 0
    answers: list[QAAnswerResponse] = Field(default_factory=list)
    answer: str | None = Field(default=None, max_length=MAX_ANSWER_LENGTH)
    answered_by: UUID | None = None
    answered_by_display_name: str | None = Field(default=None, max_length=80)
    answered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
