"""Application orchestration for video processing and grounded chat."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.documents import Document

from .answer_service import AnswerService
from .chunking_service import ChunkingService
from .retrieval_service import RetrievalService, VectorStore
from .transcript_service import TranscriptService


class VideoNotProcessedError(Exception):
    """Raised when chat is requested for a video without an in-memory index."""


class NoRelevantContextError(Exception):
    """Raised when retrieval returns no transcript documents."""


class AnswerGenerationError(Exception):
    """Raised when the language model cannot generate an answer."""


class AnswerProviderConfigurationError(Exception):
    """Raised when the language model credentials are missing or rejected."""


@dataclass(frozen=True, slots=True)
class ProcessedVideo:
    video_id: str
    status: str
    chunk_count: int


@dataclass(frozen=True, slots=True)
class ChatAnswer:
    answer: str
    sources: tuple[Document, ...]


class AssistantService:
    """Coordinate transcript ingestion, retrieval, and grounded answering."""

    def __init__(
        self,
        transcript_service: TranscriptService | None = None,
        chunking_service: ChunkingService | None = None,
        retrieval_service: RetrievalService | None = None,
        answer_service: AnswerService | None = None,
    ) -> None:
        self._transcript_service = transcript_service or TranscriptService()
        self._chunking_service = chunking_service or ChunkingService()
        self._retrieval_service = retrieval_service or RetrievalService()
        self._answer_service = answer_service
        self._indexes: dict[str, VectorStore] = {}

    def process_video(self, source: str, languages: list[str]) -> ProcessedVideo:
        transcript = self._transcript_service.fetch(source, languages=languages)
        documents = self._chunking_service.chunk(transcript)
        vector_store = self._retrieval_service.build_index(documents)
        self._indexes[transcript.video_id] = vector_store
        return ProcessedVideo(
            video_id=transcript.video_id,
            status="ready",
            chunk_count=len(documents),
        )

    def chat(self, video_id: str, question: str) -> ChatAnswer:
        vector_store = self._indexes.get(video_id)
        if vector_store is None:
            raise VideoNotProcessedError(video_id)

        documents = self._retrieval_service.retrieve(question, vector_store)
        try:
            answer_service = self._answer_service or AnswerService()
            answer = answer_service.answer(question, documents)
        except Exception as error:
            if _is_provider_configuration_error(error):
                raise AnswerProviderConfigurationError from error
            raise AnswerGenerationError from error
        return ChatAnswer(answer=answer, sources=tuple(documents))


def _is_provider_configuration_error(error: Exception) -> bool:
    message = str(error).lower()
    return any(
        marker in message
        for marker in (
            "googleauthenticationerror",
            "api key",
            "unauthorized",
            "invalid api key",
            "permission denied",
        )
    )