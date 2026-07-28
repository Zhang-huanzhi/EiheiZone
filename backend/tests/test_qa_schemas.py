import pytest
from pydantic import ValidationError

from app.modules.qas.schemas import QACreate, QAAnswerUpsert


@pytest.mark.parametrize("value", ["q", "q" * 2000, "Question with\nformatting"])
def test_qa_create_accepts_valid_question_boundaries(value: str) -> None:
    assert QACreate(question=value).question == value


@pytest.mark.parametrize("value", ["", "   ", "q" * 2001])
def test_qa_create_rejects_invalid_question_text(value: str) -> None:
    with pytest.raises(ValidationError):
        QACreate(question=value)


@pytest.mark.parametrize("value", ["a", "a" * 10000, "Answer with\nformatting"])
def test_qa_answer_accepts_valid_answer_boundaries(value: str) -> None:
    assert QAAnswerUpsert(answer=value).answer == value


@pytest.mark.parametrize("value", ["", "\n\t", "a" * 10001])
def test_qa_answer_rejects_invalid_answer_text(value: str) -> None:
    with pytest.raises(ValidationError):
        QAAnswerUpsert(answer=value)
