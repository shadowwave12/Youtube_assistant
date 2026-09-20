"""Build and query the notebook's in-memory FAISS retrieval index."""

from __future__ import annotations

from typing import Any, Callable, Protocol, Sequence

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings


class Retriever(Protocol):
    def invoke(self, query: str) -> list[Document]: ...


class VectorStore(Protocol):
    def as_retriever(self, *, search_type: str, search_kwargs: dict[str, int]) -> Retriever: ...


VectorStoreFactory = Callable[[Sequence[Document], Embeddings], VectorStore]


class RetrievalService:
    """Create an in-memory index and retrieve the four most similar chunks."""

    def __init__(
        self,
        embedding_model: Embeddings | None = None,
        vector_store_factory: VectorStoreFactory | None = None,
        top_k: int = 4,
    ) -> None:
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")
        self._embedding_model = embedding_model or HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self._vector_store_factory = vector_store_factory or _create_faiss_store
        self._top_k = top_k

    def build_index(self, documents: Sequence[Document]) -> VectorStore:
        """Build an in-memory vector store from chunked documents."""

        if not documents:
            raise ValueError("At least one document is required to build an index.")
        return self._vector_store_factory(documents, self._embedding_model)

    def retrieve(self, query: str, vector_store: VectorStore) -> list[Document]:
        """Retrieve documents using similarity search with the configured top-k."""

        if not query.strip():
            raise ValueError("A retrieval query is required.")
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self._top_k},
        )
        return retriever.invoke(query)


def _create_faiss_store(documents: Sequence[Document], embedding_model: Embeddings) -> VectorStore:
    return FAISS.from_documents(list(documents), embedding_model)