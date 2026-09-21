"""Pydantic request and response models for the public API."""

from pydantic import BaseModel, Field


class ProcessVideoRequest(BaseModel):
    source: str = Field(
        ...,
        min_length=1,
        description="A YouTube URL or 11-character video ID.",
        examples=["https://www.youtube.com/watch?v=4Vz6L8B73i4"],
    )
    languages: list[str] = Field(
        default=["en"],
        min_length=1,
        description="Transcript language codes, tried in the provided order.",
        examples=[["en"]],
    )


class ProcessVideoResponse(BaseModel):
    video_id: str = Field(..., description="The normalized YouTube video ID.")
    status: str = Field(..., description="Processing status.", examples=["ready"])
    chunk_count: int = Field(..., ge=1, description="Number of indexed transcript chunks.")


class ChatRequest(BaseModel):
    video_id: str = Field(..., min_length=11, max_length=11, description="Processed YouTube video ID.")
    question: str = Field(..., min_length=1, description="Question to answer from the transcript.")


class SourceReference(BaseModel):
    text: str
    video_id: str
    chunk_index: int = Field(..., ge=0)
    segments: list["SourceSegment"] = Field(
        default_factory=list,
        description="Transcript segments contributing to this source, including original timing.",
    )


class SourceSegment(BaseModel):
    text: str
    start: float | None = None
    duration: float | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceReference]