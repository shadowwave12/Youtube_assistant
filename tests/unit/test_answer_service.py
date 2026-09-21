from dataclasses import dataclass

import pytest
from langchain_core.documents import Document

from backend.app.services.answer_service import (
    AnswerService,
    INSUFFICIENT_CONTEXT_RESPONSE,
    _clean_answer,
)


@dataclass
class FakeResponse:
    content: str


class FakePrompt:
    def __init__(self) -> None:
        self.calls = []

    def invoke(self, values):
        self.calls.append(values)
        return values


class FakeLanguageModel:
    def __init__(self) -> None:
        self.calls = []

    def invoke(self, prompt):
        self.calls.append(prompt)
        return FakeResponse("The grounded answer.")


def test_answer_uses_only_retrieved_text_and_preserves_metadata_on_documents() -> None:
    prompt = FakePrompt()
    model = FakeLanguageModel()
    documents = [
        Document(page_content="First context", metadata={"video_id": "abc", "chunk_index": 0}),
        Document(page_content="Second context", metadata={"video_id": "abc", "chunk_index": 1}),
    ]

    result = AnswerService(language_model=model, prompt=prompt).answer("What happened?", documents)

    assert result == "The grounded answer."
    assert prompt.calls[0]["context"] == "First context\n\nSecond context"
    assert prompt.calls[0]["question"] == "What happened?"
    assert prompt.calls[0]["insufficient_context_response"] == INSUFFICIENT_CONTEXT_RESPONSE
    assert documents[0].metadata["video_id"] == "abc"
    assert model.calls == prompt.calls


def test_answer_rejects_empty_question_or_context() -> None:
    service = AnswerService(language_model=FakeLanguageModel(), prompt=FakePrompt())

    with pytest.raises(ValueError):
        service.answer(" ", [Document(page_content="context")])
    assert service.answer("Question?", []) == INSUFFICIENT_CONTEXT_RESPONSE


def test_answer_uses_explicit_insufficient_context_response() -> None:
    prompt = FakePrompt()
    model = FakeLanguageModel()
    model.invoke = lambda prompt_value: FakeResponse(INSUFFICIENT_CONTEXT_RESPONSE)

    answer = AnswerService(language_model=model, prompt=prompt).answer(
        "What is not discussed?",
        [Document(page_content="The transcript discusses lesson planning.")],
    )

    assert answer == INSUFFICIENT_CONTEXT_RESPONSE
    assert "source" not in answer.lower()
    assert "timestamp" not in answer.lower()


def test_clean_answer_normalizes_newlines_and_removes_placeholders() -> None:
    raw = "Here is the answer\\n\\n{answer}\\n[source]\\nThis is a short summary."

    cleaned = _clean_answer(raw)

    assert "{answer}" not in cleaned
    assert "[source]" not in cleaned
    assert "\\n" not in cleaned
    assert "This is a short summary." in cleaned


def test_clean_answer_removes_citation_artifacts_and_keeps_markdown() -> None:
    raw = "## Key idea\n\n- First point\n- Second point\n\n[source]\n\n**Important**: execution matters."

    cleaned = _clean_answer(raw)

    assert cleaned.startswith("## Key idea")
    assert "**Important**" in cleaned
    assert "[source]" not in cleaned
    assert "Key idea" in cleaned


def test_clean_answer_returns_insufficient_context_for_empty_or_invalid_output() -> None:
    assert _clean_answer("   ") == INSUFFICIENT_CONTEXT_RESPONSE
    assert _clean_answer("{context}") == INSUFFICIENT_CONTEXT_RESPONSE