"""Split fetched transcripts into metadata-preserving documents."""

from __future__ import annotations

from typing import Any, Protocol, Sequence

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .transcript_service import Transcript


class TextSplitter(Protocol):
    def create_documents(
        self, texts: Sequence[str], metadatas: Sequence[dict[str, Any]] | None = None
    ) -> list[Document]: ...


class ChunkingService:
    """Apply the notebook's initial chunking configuration to a transcript."""

    def __init__(self, splitter: TextSplitter | None = None) -> None:
        self._splitter = splitter or RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )

    def chunk(self, transcript: Transcript) -> list[Document]:
        """Return split transcript documents with their source metadata preserved."""

        # A chunk is a smaller piece of the transcript that can be searched later.
        # Timing metadata lets the API return useful source information.
        source_metadata = {
            "video_id": transcript.video_id,
            "segments": [
                {
                    "text": segment.text,
                    "start": segment.start,
                    "duration": segment.duration,
                }
                for segment in transcript.segments
            ],
        }
        text = " ".join(segment.text for segment in transcript.segments)
        documents = self._splitter.create_documents([text], metadatas=[source_metadata])

        for chunk_index, document in enumerate(documents):
            document.metadata["chunk_index"] = chunk_index
        return documents