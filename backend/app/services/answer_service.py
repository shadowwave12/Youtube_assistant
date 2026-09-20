"""Generate answers grounded in retrieved transcript documents."""

from __future__ import annotations

from typing import Any, Protocol, Sequence

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI


class LanguageModel(Protocol):
    def invoke(self, prompt: Any) -> Any: ...


class AnswerService:
    """Format retrieved context and ask the configured model for a grounded answer."""

    def __init__(
        self,
        language_model: LanguageModel | None = None,
        prompt: Any | None = None,
    ) -> None:
        self._language_model = language_model or ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            temperature=0.2,
        )
        self._prompt = prompt or PromptTemplate(
            template="""
      You are a helpful assistant.
      Answer ONLY from the provided transcript context.
      If the context is insufficient, just say you don't know.

      {context}
      Question: {question}
    """,
            input_variables=["context", "question"],
        )

    def answer(self, question: str, documents: Sequence[Document]) -> str:
        """Return a model answer grounded only in the retrieved document text."""

        if not question.strip():
            raise ValueError("A question is required.")
        if not documents:
            raise ValueError("At least one retrieved document is required.")

        context = "\n\n".join(document.page_content for document in documents)
        prompt_value = self._prompt.invoke({"context": context, "question": question})
        response = self._language_model.invoke(prompt_value)
        content = getattr(response, "content", response)
        return str(content)