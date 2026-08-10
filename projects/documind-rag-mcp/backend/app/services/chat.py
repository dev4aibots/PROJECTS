"""Chat service: the full grounded question-answering pipeline.

screen -> embed -> retrieve -> shape -> evidence gate -> LLM -> deterministic
citation validation -> persist. The LLM sits BETWEEN two deterministic gates;
it can neither see ungated input nor emit unvalidated citations.
"""

from __future__ import annotations

import time
from typing import Optional
from uuid import UUID

from ..core.errors import NotFoundError
from ..core.observability import EventObserver, NoopObserver
from ..domain.models import (
    Conversation,
    GroundedAnswer,
    Message,
    RetrievalLog,
    make_refusal,
)
from ..domain.retrieval_shaping import (
    compute_confidence,
    evidence_sufficient,
    shape_retrieval,
)
from ..domain.screening import screen_question
from ..providers.protocols import ChatProvider, EmbeddingProvider
from ..repositories.protocols import (
    ChunkRepository,
    ConversationRepository,
    RetrievalLogRepository,
)


class ChatService:
    def __init__(
        self,
        conversations: ConversationRepository,
        chunks: ChunkRepository,
        retrieval_logs: RetrievalLogRepository,
        embeddings: EmbeddingProvider,
        chat: ChatProvider,
        top_k: int = 8,
        similarity_threshold: float = 0.35,
        context_token_cap: int = 4000,
        max_question_chars: int = 2000,
        observer: EventObserver | None = None,
    ) -> None:
        self._conversations = conversations
        self._chunks = chunks
        self._retrieval_logs = retrieval_logs
        self._embeddings = embeddings
        self._chat = chat
        self._top_k = top_k
        self._similarity_threshold = similarity_threshold
        self._context_token_cap = context_token_cap
        self._max_question_chars = max_question_chars
        self._observer = observer or NoopObserver()

    async def start_conversation(self, session_id: UUID) -> Conversation:
        return await self._conversations.create(Conversation(session_id=session_id))

    async def get_conversation(
        self, conversation_id: UUID, session_id: UUID
    ) -> Conversation:
        conv = await self._conversations.get(conversation_id, session_id)
        if conv is None:
            raise NotFoundError("Conversation not found.")
        return conv

    async def list_messages(
        self, conversation_id: UUID, session_id: UUID
    ) -> list[dict]:
        await self.get_conversation(conversation_id, session_id)
        messages = await self._conversations.list_messages(conversation_id)
        out = []
        for m in messages:
            citations = (
                await self._conversations.list_citations(m.id)
                if m.role == "assistant"
                else []
            )
            out.append(
                {
                    "id": str(m.id),
                    "role": m.role,
                    "content": m.content,
                    "grounded": m.grounded,
                    "confidence": m.confidence,
                    "citations": citations,
                    "created_at": m.created_at.isoformat(),
                }
            )
        return out

    async def get_retrieval(self, message_id: UUID, session_id: UUID) -> RetrievalLog:
        message = await self._conversations.get_message_for_session(message_id, session_id)
        if message is None or message.role != "assistant":
            raise NotFoundError("Retrieval record not found.")
        log = await self._retrieval_logs.get_for_message(message_id)
        if log is None:
            raise NotFoundError("Retrieval record not found.")
        return log

    async def search(
        self,
        session_id: UUID,
        query: str,
        top_k: int | None = None,
        filter_document_ids: Optional[list[UUID]] = None,
    ) -> list[dict]:
        """Return session-scoped shaped evidence for REST/MCP inspection."""
        cleaned = screen_question(query, self._max_question_chars)
        query_embedding = await self._embeddings.embed_query(cleaned)
        hits = await self._chunks.match(
            query_embedding,
            match_count=min(top_k or self._top_k, 50),
            similarity_threshold=self._similarity_threshold,
            session_id=session_id,
            filter_document_ids=filter_document_ids,
        )
        return [chunk.model_dump(mode="json") for chunk in shape_retrieval(hits, self._context_token_cap)]

    async def ask(
        self,
        conversation_id: UUID,
        session_id: UUID,
        question: str,
        filter_document_ids: Optional[list[UUID]] = None,
    ) -> tuple[Message, GroundedAnswer]:
        """Run the full pipeline. Returns the persisted assistant message + answer."""
        await self.get_conversation(conversation_id, session_id)
        cleaned = screen_question(question, self._max_question_chars)

        # Persist the user turn first: even refusals leave an honest history.
        await self._conversations.add_message(
            Message(conversation_id=conversation_id, role="user", content=cleaned)
        )

        started = time.monotonic()
        query_embedding = await self._embeddings.embed_query(cleaned)
        raw_hits = await self._chunks.match(
            query_embedding,
            match_count=self._top_k,
            similarity_threshold=self._similarity_threshold,
            session_id=session_id,
            filter_document_ids=filter_document_ids,
        )
        evidence = shape_retrieval(raw_hits, token_cap=self._context_token_cap)
        duration_ms = int((time.monotonic() - started) * 1000)

        if not evidence_sufficient(evidence):
            answer = make_refusal()
        else:
            confidence = compute_confidence(evidence)
            draft = await self._chat.answer(cleaned, evidence)
            from ..domain.citations import validate_citations

            validation = validate_citations(draft, evidence, confidence)
            answer = validation.answer
            if validation.violation:
                await self._observer.emit(
                    "citation_violation",
                    {
                        "conversation_id": str(conversation_id),
                        "stripped_count": validation.stripped_count,
                        "retrieved_count": len(evidence),
                    },
                )

        assistant = await self._conversations.add_message(
            Message(
                conversation_id=conversation_id,
                role="assistant",
                content=answer.answer,
                grounded=answer.grounded,
                confidence=answer.confidence,
            )
        )
        if answer.citations:
            await self._conversations.add_citations(
                assistant.id,
                [
                    {
                        "document_id": str(c.document_id),
                        "filename": c.filename,
                        "page": c.page,
                        "excerpt": c.excerpt,
                        "chunk_id": str(c.chunk_id) if c.chunk_id else None,
                    }
                    for c in answer.citations
                ],
            )

        await self._retrieval_logs.create(
            RetrievalLog(
                message_id=assistant.id,
                query=cleaned,
                top_k=self._top_k,
                threshold=self._similarity_threshold,
                returned_count=len(evidence),
                max_similarity=max((c.similarity for c in evidence), default=None),
                duration_ms=duration_ms,
            )
        )
        return assistant, answer
