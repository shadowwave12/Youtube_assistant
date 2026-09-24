"""Fetch and normalize YouTube transcripts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Protocol, Sequence
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApiException,
)


class TranscriptServiceError(Exception):
    """Base class for expected transcript service failures."""


class InvalidVideoSourceError(TranscriptServiceError):
    """The supplied value is not a supported YouTube URL or video ID."""


class TranscriptNotFoundError(TranscriptServiceError):
    """The video has no transcript available."""


class TranscriptsDisabledError(TranscriptServiceError):
    """The video owner has disabled transcripts."""


class UnsupportedTranscriptLanguageError(TranscriptServiceError):
    """The requested language is not available for the video."""


class TranscriptFetchError(TranscriptServiceError):
    """The provider failed while retrieving a transcript."""


@dataclass(frozen=True, slots=True)
class TranscriptSegment:
    """One transcript snippet with optional timing metadata."""

    text: str
    start: float | None
    duration: float | None


@dataclass(frozen=True, slots=True)
class Transcript:
    """A normalized transcript returned by the service."""

    video_id: str
    segments: tuple[TranscriptSegment, ...]


class TranscriptApiClient(Protocol):
    def fetch(self, video_id: str, languages: Sequence[str]) -> Iterable[Any]: ...


_VIDEO_ID_LENGTH = 11
_YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}


def extract_video_id(source: str) -> str:
    """Extract and validate a YouTube video ID from a URL or raw ID."""

    value = source.strip()
    if not value:
        raise InvalidVideoSourceError("A YouTube URL or video ID is required.")

    if _is_video_id(value):
        return value

    parsed = urlparse(value)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme not in {"http", "https"} or hostname not in _YOUTUBE_HOSTS:
        raise InvalidVideoSourceError("The source must be a YouTube URL or video ID.")

    if hostname == "youtu.be":
        candidate = parsed.path.strip("/").split("/")[0]
    elif parsed.path == "/watch":
        candidate = parse_qs(parsed.query).get("v", [""])[0]
    else:
        path_parts = [part for part in parsed.path.split("/") if part]
        candidate = path_parts[1] if len(path_parts) >= 2 and path_parts[0] in {"embed", "shorts", "live"} else ""

    if not _is_video_id(candidate):
        raise InvalidVideoSourceError("The YouTube URL does not contain a valid video ID.")
    return candidate


def _is_video_id(value: str) -> bool:
    return len(value) == _VIDEO_ID_LENGTH and all(character.isalnum() or character in "-_" for character in value)


class TranscriptService:
    """Application-facing transcript retrieval service."""

    def __init__(self, api_client: TranscriptApiClient | None = None) -> None:
        self._api_client = api_client or YouTubeTranscriptApi()

    def fetch(self, source: str, languages: Sequence[str] = ("en",)) -> Transcript:
        video_id = extract_video_id(source)
        requested_languages = tuple(language.strip() for language in languages if language.strip())
        if not requested_languages:
            raise UnsupportedTranscriptLanguageError("At least one transcript language is required.")

        try:
            raw_segments = tuple(self._api_client.fetch(video_id, languages=requested_languages))
        except TranscriptsDisabled as error:
            raise TranscriptsDisabledError(f"Transcripts are disabled for video {video_id}.") from error
        except NoTranscriptFound as error:
            available = getattr(error, "available_transcripts", None)
            if available:
                raise UnsupportedTranscriptLanguageError(
                    f"No requested transcript language is available for video {video_id}."
                ) from error
            raise TranscriptNotFoundError(f"No transcript is available for video {video_id}.") from error
        except (VideoUnavailable, CouldNotRetrieveTranscript, YouTubeTranscriptApiException) as error:
            import traceback
            traceback.print_exc() 
            raise TranscriptFetchError(f"Could not fetch the transcript for video {video_id}.") from error

        segments = tuple(_to_segment(segment) for segment in raw_segments)
        if not segments:
            raise TranscriptNotFoundError(f"No transcript is available for video {video_id}.")
        return Transcript(video_id=video_id, segments=segments)


def _to_segment(raw_segment: Any) -> TranscriptSegment:
    return TranscriptSegment(
        text=str(_read_value(raw_segment, "text", "")),
        start=_optional_float(_read_value(raw_segment, "start")),
        duration=_optional_float(_read_value(raw_segment, "duration")),
    )


def _read_value(raw_segment: Any, name: str, default: Any = None) -> Any:
    if isinstance(raw_segment, dict):
        return raw_segment.get(name, default)
    return getattr(raw_segment, name, default)


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)