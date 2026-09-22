"""Application orchestration for video processing and grounded chat."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from langchain_core.documents import Document

from .answer_service import AnswerService
from .chunking_service import ChunkingService
from .retrieval_service import RetrievalService, VectorStore
from .transcript_service import TranscriptService

logger = logging.getLogger(__name__)


class VideoNotProcessedError(Exception):
    """Raised when chat is requested for a video without an in-memory index."""


class NoRelevantContextError(Exception):
    """Raised when retrieval returns no transcript documents."""


class AnswerGenerationError(Exception):
    """Raised when the language model cannot generate an answer."""

    def __init__(
        self,
        message: str = "The answer provider could not generate a response.",
        *,
        code: str = "LLM_PROVIDER_ERROR",
        status_code: int = 502,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.request_id = request_id

    def to_response(self) -> dict[str, object]:
        return {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message,
                "request_id": self.request_id,
            },
            "detail": self.message,
        }


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
        logger.info("[VIDEO] Processing source")
        transcript = self._transcript_service.fetch(source, languages=languages)
        logger.info("[TRANSCRIPT] Retrieved video_id=%s segments=%d", transcript.video_id, len(transcript.segments))
        documents = self._chunking_service.chunk(transcript)
        logger.info("[CHUNKING] Created chunks=%d video_id=%s", len(documents), transcript.video_id)
        vector_store = self._retrieval_service.build_index(documents)
        logger.info("[VECTORSTORE] Index created video_id=%s", transcript.video_id)
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
        logger.info("[RETRIEVAL] Retrieved chunks=%d video_id=%s", len(documents), video_id)
        try:
            answer_service = self._answer_service or AnswerService()
            logger.info("[LLM] Request started")
            answer = answer_service.answer(question, documents)
            logger.info("[ANSWER] Response normalized")
        except Exception as error:
            logger.exception("[LLM] Request failed")
            if _is_provider_configuration_error(error):
                raise AnswerProviderConfigurationError from error
            raise _classify_llm_error(error) from error
        return ChatAnswer(answer=answer, sources=tuple(documents))


def _classify_llm_error(error: Exception) -> AnswerGenerationError:
    message = str(error)
    lower = message.lower()
    if any(
        marker in lower
        for marker in (
            "invalid request",
            "invalid model",
            "unsupported model",
            "model not found",
            "modelnotfound",
            "not_found",
        )
    ):
        return AnswerGenerationError(
            "The configured model is invalid for this provider.",
            code="LLM_MODEL_ERROR",
            status_code=400,
            request_id=_make_request_id(),
        )
    if any(marker in lower for marker in ("429", "rate limit", "too many requests")):
        return AnswerGenerationError(
            "The language model provider is rate-limiting requests.",
            code="LLM_RATE_LIMIT",
            status_code=429,
            request_id=_make_request_id(),
        )
    if any(marker in lower for marker in ("timeout", "timed out", "read timed out")):
        return AnswerGenerationError(
            "The language model request timed out.",
            code="LLM_TIMEOUT",
            status_code=504,
            request_id=_make_request_id(),
        )
    if any(marker in lower for marker in ("auth", "api key", "unauthorized", "invalid api key", "forbidden")):
        return AnswerGenerationError(
            "The language model provider rejected the API credentials.",
            code="LLM_AUTH_ERROR",
            status_code=401,
            request_id=_make_request_id(),
        )
    if any(marker in lower for marker in ("connection", "network", "dns", "temporary failure")):
        return AnswerGenerationError(
            "The language model provider could not be reached.",
            code="LLM_NETWORK_ERROR",
            status_code=502,
            request_id=_make_request_id(),
        )
    if any(marker in lower for marker in ("500", "internal server error", "upstream error")):
        return AnswerGenerationError(
            "The language model provider returned a server error.",
            code="LLM_SERVER_ERROR",
            status_code=502,
            request_id=_make_request_id(),
        )
    if not message or message.strip() == "":
        return AnswerGenerationError(
            "The language model returned an empty response.",
            code="LLM_EMPTY_RESPONSE",
            status_code=502,
            request_id=_make_request_id(),
        )
    return AnswerGenerationError(
        "The answer provider could not generate a response.",
        code="LLM_PROVIDER_ERROR",
        status_code=502,
        request_id=_make_request_id(),
    )


def _make_request_id() -> str:
    import uuid

    return uuid.uuid4().hex


def _is_provider_configuration_error(error: Exception) -> bool:
    message = str(error).lower()
    return any(
        marker in message
        for marker in (
            "unsupported llm provider",
            "llm_api_key",
            "missing llm api key",
            "invalid llm configuration",
            "invalid model",
            "unsupported model",
            "googleauthenticationerror",
            "api key",
            "unauthorized",
            "invalid api key",
            "permission denied",
            "authentication",
        )
    )