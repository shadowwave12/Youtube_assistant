from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from backend.app.dependencies import get_assistant_service
from backend.app.main import app
from backend.app.services.assistant_service import (
    AnswerGenerationError,
    AnswerProviderConfigurationError,
    ChatAnswer,
    NoRelevantContextError,
    ProcessedVideo,
    VideoNotProcessedError,
)
from backend.app.services.transcript_service import InvalidVideoSourceError


@dataclass
class FakeAssistantService:
    process_result: ProcessedVideo | None = None
    chat_result: ChatAnswer | None = None
    process_error: Exception | None = None
    chat_error: Exception | None = None

    def process_video(self, source: str, languages: list[str]) -> ProcessedVideo:
        if self.process_error:
            raise self.process_error
        assert source
        assert languages == ["en"]
        return self.process_result or ProcessedVideo("4Vz6L8B73i4", "ready", 3)

    def chat(self, video_id: str, question: str) -> ChatAnswer:
        if self.chat_error:
            raise self.chat_error
        assert video_id == "4Vz6L8B73i4"
        assert question
        return self.chat_result or ChatAnswer(
            answer="The grounded answer.",
            sources=(
                Document(
                    page_content="Transcript context",
                    metadata={
                        "video_id": video_id,
                        "chunk_index": 0,
                        "segments": [
                            {"text": "Transcript context", "start": 12.5, "duration": 4.0}
                        ],
                    },
                ),
            ),
        )


@pytest.fixture
def client():
    service = FakeAssistantService()
    app.dependency_overrides[get_assistant_service] = lambda: service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["llm"] == {
        "provider": None,
        "model": None,
        "configured": False,
    }


def test_process_video_success(client: TestClient) -> None:
    response = client.post(
        "/api/videos/process",
        json={"source": "https://www.youtube.com/watch?v=4Vz6L8B73i4"},
    )

    assert response.status_code == 200
    assert response.json() == {"video_id": "4Vz6L8B73i4", "status": "ready", "chunk_count": 3}


def test_process_video_rejects_invalid_source(client: TestClient) -> None:
    app.dependency_overrides[get_assistant_service] = lambda: FakeAssistantService(
        process_error=InvalidVideoSourceError("invalid")
    )

    response = client.post("/api/videos/process", json={"source": "not-youtube"})

    assert response.status_code == 400
    assert response.json() == {"detail": "invalid"}


def test_process_video_rejects_invalid_request_shape(client: TestClient) -> None:
    response = client.post("/api/videos/process", json={"source": ""})

    assert response.status_code == 422


def test_chat_success_returns_answer_and_sources(client: TestClient) -> None:
    response = client.post(
        "/api/chat",
        json={"video_id": "4Vz6L8B73i4", "question": "What happened?"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "The grounded answer.",
        "sources": [
            {
                "text": "Transcript context",
                "video_id": "4Vz6L8B73i4",
                "chunk_index": 0,
                "segments": [{"text": "Transcript context", "start": 12.5, "duration": 4.0}],
            }
        ],
    }


def test_chat_sources_preserve_transcript_timestamps(client: TestClient) -> None:
    response = client.post(
        "/api/chat",
        json={"video_id": "4Vz6L8B73i4", "question": "Where is this discussed?"},
    )

    assert response.status_code == 200
    assert response.json()["sources"][0]["segments"] == [
        {"text": "Transcript context", "start": 12.5, "duration": 4.0}
    ]


def test_chat_returns_explicit_insufficient_context_response(client: TestClient) -> None:
    class EmptyContextService(FakeAssistantService):
        def chat(self, video_id: str, question: str) -> ChatAnswer:
            return ChatAnswer(
                answer="Insufficient context: the retrieved transcript does not support an answer to this question.",
                sources=(),
            )

    app.dependency_overrides[get_assistant_service] = lambda: EmptyContextService()

    response = client.post(
        "/api/chat",
        json={"video_id": "4Vz6L8B73i4", "question": "What is not discussed?"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Insufficient context: the retrieved transcript does not support an answer to this question.",
        "sources": [],
    }


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_detail"),
    [
        (VideoNotProcessedError("missing"), 404, "Process this video before asking questions."),
        (NoRelevantContextError("empty"), 404, "No relevant transcript context was found."),
        (AnswerGenerationError(), 502, "The answer provider could not generate a response."),
        (AnswerProviderConfigurationError(), 503, "The configured language model provider is invalid or rejected the request. Check backend/.env and restart FastAPI."),
    ],
)
def test_chat_maps_common_failures(client: TestClient, error: Exception, expected_status: int, expected_detail: str) -> None:
    app.dependency_overrides[get_assistant_service] = lambda: FakeAssistantService(chat_error=error)

    response = client.post(
        "/api/chat",
        json={"video_id": "4Vz6L8B73i4", "question": "What happened?"},
    )

    assert response.status_code == expected_status
    payload = response.json()
    if isinstance(payload["detail"], str):
        assert payload["detail"] == expected_detail
    else:
        assert payload["detail"]["error"]["message"] == expected_detail