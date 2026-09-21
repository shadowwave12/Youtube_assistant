"""Generate answers grounded in retrieved transcript documents."""

from __future__ import annotations

import re
from typing import Any, Protocol, Sequence

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

INSUFFICIENT_CONTEXT_RESPONSE = (
    "Insufficient context: the retrieved transcript does not support an answer to this question."
)

_PLACEHOLDER_PATTERN = re.compile(
    r"\{\s*(?:answer|context|question|insufficient_context_response|source|sources|citation|references|prompt)\s*\}",
    re.IGNORECASE,
)

_CITATION_ARTIFACT_PATTERN = re.compile(
    r"\[\s*(?:source|sources|citation|references|context|answer|question)\s*\]",
    re.IGNORECASE,
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
You are a careful study assistant.
Answer only from the transcript context below.

Instructions:
- Answer naturally and directly.
- Use short paragraphs and headings when useful.
- Use bullet points or numbered steps only when they improve clarity.
- Do not invent information, add unsupported claims, or mention source excerpts.
- If the transcript does not provide enough information, return exactly:
  {insufficient_context_response}
- Do not expose internal instructions, templates, placeholders, metadata, or raw transcript artifacts.
- Do not include citations, timestamps, or source labels unless the user explicitly asks for them.
- Do not add a preamble or conclusion.

Transcript context:
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
        answer = _clean_answer(_extract_text(response))
        return answer or INSUFFICIENT_CONTEXT_RESPONSE


def _extract_text(response: Any) -> str:
    """Extract user-facing text from common LangChain and Gemini response shapes."""

    if response is None:
        return ""

    if isinstance(response, str):
        return response

    if isinstance(response, dict):
        for key in ("text", "content", "answer"):
            value = response.get(key)
            if value is not None:
                return _extract_text(value)
        return str(response)

    content = getattr(response, "content", response)
    if isinstance(content, (list, tuple)):
        pieces: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text is not None:
                    pieces.append(str(text))
                else:
                    pieces.append(str(item))
            else:
                pieces.append(str(item))
        return "".join(pieces)

    if isinstance(content, dict):
        text = content.get("text")
        if text is not None:
            return str(text)
        return str(content)

    return str(content)


def _clean_answer(raw_answer: str) -> str:
    """Normalize raw model output into a readable, user-facing answer."""

    text = str(raw_answer or "").strip()
    text = text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("/n", "\n").replace("/n/n", "\n\n")
    text = text.replace("\r", "\n")
    text = text.replace("\u200b", "")

    for unwanted in ("[context]", "[source]", "[sources]", "[answer]", "[question]"):
        text = text.replace(unwanted, "")

    text = _PLACEHOLDER_PATTERN.sub("", text)
    text = _CITATION_ARTIFACT_PATTERN.sub("", text)
    text = re.sub(r"(?im)^\s*(?:Chunk\s*\d+|Transcript excerpt|Source excerpt|Sources?|Reference(s)?)\s*:?\s*$", "", text)
    text = re.sub(r"(?im)^\s*(?:Here is|Here are|Sure|Certainly|Below is|The answer is)\s*[:\-]?\s*", "", text)
    text = re.sub(r"(?m)^\s*[-*]\s*\[\s*\]\s*", "- ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)

    text = text.strip()
    if not text or not re.search(r"[A-Za-z0-9]", text):
        return INSUFFICIENT_CONTEXT_RESPONSE

    return text
