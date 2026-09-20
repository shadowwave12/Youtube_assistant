from dataclasses import dataclass

import pytest

from backend.app.services import transcript_service as service_module
from backend.app.services.transcript_service import (
    InvalidVideoSourceError,
    TranscriptNotFoundError,
    TranscriptService,
    TranscriptsDisabledError,
    UnsupportedTranscriptLanguageError,
    extract_video_id,
)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("4Vz6L8B73i4", "4Vz6L8B73i4"),
        ("https://www.youtube.com/watch?v=4Vz6L8B73i4", "4Vz6L8B73i4"),
        ("https://youtu.be/4Vz6L8B73i4?t=30", "4Vz6L8B73i4"),
        ("https://www.youtube.com/shorts/4Vz6L8B73i4", "4Vz6L8B73i4"),
        ("https://www.youtube.com/embed/4Vz6L8B73i4", "4Vz6L8B73i4"),
    ],
)
def test_extract_video_id_accepts_supported_sources(source: str, expected: str) -> None:
    assert extract_video_id(source) == expected


@pytest.mark.parametrize(
    "source",
    ["", "not a video", "https://example.com/watch?v=4Vz6L8B73i4", "https://youtu.be/short"],
)
def test_extract_video_id_rejects_invalid_sources(source: str) -> None:
    with pytest.raises(InvalidVideoSourceError):
        extract_video_id(source)


@dataclass
class FakeSegment:
    text: str
    start: float
    duration: float


class FakeApi:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def fetch(self, video_id: str, languages: tuple[str, ...]):
        self.calls.append((video_id, languages))
        if self.error:
            raise self.error
        return self.result


def test_fetch_returns_typed_segments_and_preserves_timing() -> None:
    api = FakeApi([FakeSegment("Hello", 1.5, 2.0), {"text": "world"}])

    transcript = TranscriptService(api).fetch("4Vz6L8B73i4", languages=("en", "en-US"))

    assert transcript.video_id == "4Vz6L8B73i4"
    assert transcript.segments[0].text == "Hello"
    assert transcript.segments[0].start == 1.5
    assert transcript.segments[0].duration == 2.0
    assert transcript.segments[1].start is None
    assert api.calls == [("4Vz6L8B73i4", ("en", "en-US"))]


def test_fetch_maps_disabled_transcripts(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeDisabled(Exception):
        pass

    monkeypatch.setattr(service_module, "TranscriptsDisabled", FakeDisabled)

    with pytest.raises(TranscriptsDisabledError):
        TranscriptService(FakeApi(error=FakeDisabled())).fetch("4Vz6L8B73i4")


def test_fetch_maps_missing_transcripts(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeMissing(Exception):
        available_transcripts = []

    monkeypatch.setattr(service_module, "NoTranscriptFound", FakeMissing)

    with pytest.raises(TranscriptNotFoundError):
        TranscriptService(FakeApi(error=FakeMissing())).fetch("4Vz6L8B73i4")


def test_fetch_maps_unsupported_languages(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeLanguageMissing(Exception):
        available_transcripts = ["es"]

    monkeypatch.setattr(service_module, "NoTranscriptFound", FakeLanguageMissing)

    with pytest.raises(UnsupportedTranscriptLanguageError):
        TranscriptService(FakeApi(error=FakeLanguageMissing())).fetch("4Vz6L8B73i4", languages=("en",))