import pytest
from langchain_core.documents import Document

from backend.app.services.retrieval_service import RetrievalService


class FakeRetriever:
    def __init__(self, documents):
        self.documents = documents

    def invoke(self, query):
        return self.documents


class FakeStore:
    def __init__(self, documents):
        self.documents = documents
        self.calls = []

    def as_retriever(self, *, search_type, search_kwargs):
        self.calls.append((search_type, search_kwargs))
        return FakeRetriever(self.documents)


def test_build_index_injects_documents_and_embedding_model() -> None:
    documents = [Document(page_content="context", metadata={"video_id": "abc"})]
    embedding_model = object()
    calls = []

    def factory(received_documents, received_embeddings):
        calls.append((received_documents, received_embeddings))
        return FakeStore(documents)

    service = RetrievalService(embedding_model=embedding_model, vector_store_factory=factory)
    store = service.build_index(documents)

    assert store is not None
    assert calls == [(documents, embedding_model)]


def test_retrieve_uses_similarity_and_k_six() -> None:
    documents = [Document(page_content="context", metadata={"chunk_index": 0})]
    store = FakeStore(documents)
    service = RetrievalService(embedding_model=object(), vector_store_factory=lambda *_: store)

    assert service.retrieve("What is memory?", store) == documents
    assert store.calls == [("similarity", {"k": 6})]


def test_retrieval_rejects_empty_queries_and_indexes() -> None:
    service = RetrievalService(embedding_model=object(), vector_store_factory=lambda *_: FakeStore([]))

    with pytest.raises(ValueError):
        service.build_index([])
    with pytest.raises(ValueError):
        service.retrieve(" ", FakeStore([]))