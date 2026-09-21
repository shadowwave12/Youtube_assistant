"""Generate answers grounded in retrieved transcript documents."""

from __future__ import annotations

from typing import Any, Protocol, Sequence

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

INSUFFICIENT_CONTEXT_RESPONSE = (
    "Insufficient context: the retrieved transcript does not support an answer to this question."
)


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
    If the context does not contain enough information to answer the question, return exactly:
    {insufficient_context_response}
    Do not add unsupported claims, citations, timestamps, or source references.

      {context}
      Question: {question}
    """,
            input_variables=["context", "question", "insufficient_context_response"],
        )

    def answer(self, question: str, documents: Sequence[Document]) -> str:
        """Return a model answer grounded only in the retrieved document text."""

        if not question.strip():
            raise ValueError("A question is required.")
        if not documents:
            return INSUFFICIENT_CONTEXT_RESPONSE

        context = "\n\n".join(document.page_content for document in documents)
        prompt_value = self._prompt.invoke(
            {
                "context": context,
                "question": question,
                "insufficient_context_response": INSUFFICIENT_CONTEXT_RESPONSE,
            }
        )
        response = self._language_model.invoke(prompt_value)
        content = getattr(response, "content", response)
        answer = str(content).strip()
        return answer or INSUFFICIENT_CONTEXT_RESPONSE