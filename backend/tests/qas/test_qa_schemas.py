from uuid import uuid4
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.modules.qas.models import QAStatus
from app.modules.qas.schemas import (
    QACreate,
    QAAnswerCreate,
    QAAnswerResponse,
    QAAnswerUpdate,
    QAAnswerUpsert,
    QAResponse,
)


@pytest.mark.parametrize("value", ["q", "q" * 2000, "Question with\nformatting"])
def test_qa_create_accepts_valid_question_boundaries(value: str) -> None:
    created = QACreate(question=value, is_proxy=True)
    assert created.question == value
    assert created.is_proxy is True


@pytest.mark.parametrize("value", ["", "   ", "q" * 2001])
def test_qa_create_rejects_invalid_question_text(value: str) -> None:
    with pytest.raises(ValidationError):
        QACreate(question=value)


@pytest.mark.parametrize("value", ["a", "a" * 10000, "Answer with\nformatting"])
def test_qa_answer_accepts_valid_answer_boundaries(value: str) -> None:
    assert QAAnswerUpsert(answer=value).answer == value
    created = QAAnswerCreate(content=value, is_proxy=True)
    assert created.content == value
    assert created.is_proxy is True
    updated = QAAnswerUpdate(content=value, is_proxy=False)
    assert updated.content == value
    assert updated.is_proxy is False


@pytest.mark.parametrize("value", ["", "\n\t", "a" * 10001])
def test_qa_answer_rejects_invalid_answer_text(value: str) -> None:
    with pytest.raises(ValidationError):
        QAAnswerUpsert(answer=value)
    with pytest.raises(ValidationError):
        QAAnswerCreate(content=value)
    with pytest.raises(ValidationError):
        QAAnswerUpdate(content=value)


def test_qa_response_serializes_with_answers() -> None:
    now = datetime.now(UTC)
    qa_id = uuid4()
    author_id = uuid4()
    answer_id = uuid4()
    answer = QAAnswerResponse(
        id=answer_id,
        qa_id=qa_id,
        author_id=author_id,
        author_display_name="Dad",
        content="First answer",
        is_proxy=True,
        created_at=now,
        updated_at=now,
    )
    response = QAResponse(
        id=qa_id,
        asked_by=uuid4(),
        asked_by_display_name="Me",
        question="What happened?",
        is_proxy=True,
        status=QAStatus.ANSWERED,
        answers_count=1,
        answers=[answer],
        answer="First answer",
        answered_by=author_id,
        answered_by_display_name="Dad",
        answered_at=now,
        created_at=now,
        updated_at=now,
    )
    assert response.is_proxy is True
    assert response.answers_count == 1
    assert len(response.answers) == 1
    assert response.answers[0].is_proxy is True
