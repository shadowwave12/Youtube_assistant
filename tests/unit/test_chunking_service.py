from backend.app.services.chunking_service import ChunkingService
from backend.app.services.transcript_service import Transcript, TranscriptSegment


class FakeSplitter:
    def __init__(self) -> None:
        self.calls = []

    def create_documents(self, texts, metadatas=None):
        self.calls.append((texts, metadatas))
        return [
            type("Document", (), {"page_content": texts[0], "metadata": dict(metadatas[0])})(),
        ]


def test_chunk_preserves_transcript_metadata_and_adds_chunk_index() -> None:
    splitter = FakeSplitter()
    transcript = Transcript(
        video_id="4Vz6L8B73i4",
        segments=(
            TranscriptSegment(text="Hello", start=1.5, duration=2.0),
            TranscriptSegment(text="world", start=3.5, duration=1.0),
        ),
    )

    documents = ChunkingService(splitter).chunk(transcript)

    assert documents[0].page_content == "Hello world"
    assert documents[0].metadata["video_id"] == "4Vz6L8B73i4"
    assert documents[0].metadata["segments"][0]["start"] == 1.5
    assert documents[0].metadata["segments"][1]["duration"] == 1.0
    assert documents[0].metadata["chunk_index"] == 0