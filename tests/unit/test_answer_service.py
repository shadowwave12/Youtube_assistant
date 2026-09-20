from dataclasses import dataclass

import pytest
from langchain_core.documents import Document

from backend.app.services.answer_service import AnswerService


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
    assert prompt.calls == [
        {"context": "First context\n\nSecond context", "question": "What happened?"}
    ]
    assert documents[0].metadata["video_id"] == "abc"
    assert model.calls == prompt.calls


def test_answer_rejects_empty_question_or_context() -> None:
    service = AnswerService(language_model=FakeLanguageModel(), prompt=FakePrompt())

    with pytest.raises(ValueError):
        service.answer(" ", [Document(page_content="context")])
    with pytest.raises(ValueError):
        service.answer("Question?", [])