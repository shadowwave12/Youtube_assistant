"""Thin HTTP routes for the YouTube Learning Assistant."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_assistant_service
from ..services.assistant_service import (
    AnswerGenerationError,
    AnswerProviderConfigurationError,
    AssistantService,
    NoRelevantContextError,
    VideoNotProcessedError,
)
from ..services.transcript_service import (
    InvalidVideoSourceError,
    TranscriptFetchError,
    TranscriptNotFoundError,
    TranscriptsDisabledError,
    UnsupportedTranscriptLanguageError,
)
from .schemas import (
    ChatRequest,
    ChatResponse,
    ProcessVideoRequest,
    ProcessVideoResponse,
    SourceReference,
    SourceSegment,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["assistant"])


@router.post(
    "/videos/process",
    response_model=ProcessVideoResponse,
    summary="Process a YouTube video",
    description="Fetch, chunk, embed, and index a YouTube transcript in process memory.",
)
def process_video(
    request: ProcessVideoRequest,
    service: AssistantService = Depends(get_assistant_service),
) -> ProcessVideoResponse:
    try:
        result = service.process_video(request.source, request.languages)
    except InvalidVideoSourceError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except TranscriptsDisabledError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Transcripts are disabled for this video.") from error
    except UnsupportedTranscriptLanguageError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except TranscriptNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No transcript is available for this video.") from error
    except TranscriptFetchError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="The transcript provider could not be reached.") from error
    except Exception:
        logger.exception("Video processing failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Video processing failed.")
    return ProcessVideoResponse(
        video_id=result.video_id,
        status=result.status,
        chunk_count=result.chunk_count,
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask a question about a processed video",
    description="Retrieve relevant indexed transcript chunks and generate a grounded answer.",
)
def chat(
    request: ChatRequest,
    service: AssistantService = Depends(get_assistant_service),
) -> ChatResponse:
    try:
        result = service.chat(request.video_id, request.question)
    except VideoNotProcessedError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process this video before asking questions.") from error
    except NoRelevantContextError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No relevant transcript context was found.") from error
    except AnswerGenerationError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="The answer provider could not generate a response.") from error
    except AnswerProviderConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini credentials were rejected. Update backend/.env and restart FastAPI.",
        ) from error
    except Exception:
        logger.exception("Chat request failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Chat request failed.")

    sources = [
        SourceReference(
            text=document.page_content,
            video_id=str(document.metadata.get("video_id", request.video_id)),
            chunk_index=int(document.metadata.get("chunk_index", index)),
            segments=[SourceSegment(**segment) for segment in document.metadata.get("segments", [])],
        )
        for index, document in enumerate(result.sources)
    ]
    return ChatResponse(answer=result.answer, sources=sources)