"""MCP facade that reuses REST services without duplicating business logic."""

from uuid import UUID

from .chat import ChatService
from .documents import DocumentService


class MCPFacade:
    def __init__(self, documents: DocumentService, chat: ChatService) -> None:
        self._documents = documents
        self._chat = chat

    async def list_documents(self, session_id: str) -> list[dict]:
        documents = await self._documents.list(UUID(session_id))
        return [document.model_dump(mode="json") for document in documents]

    async def search_documents(
        self,
        session_id: str,
        query: str,
        top_k: int = 8,
        document_ids: list[str] | None = None,
    ) -> list[dict]:
        return await self._chat.search(
            UUID(session_id),
            query,
            top_k,
            [UUID(document_id) for document_id in document_ids] if document_ids else None,
        )

    async def ask_documents(
        self,
        session_id: str,
        question: str,
        conversation_id: str | None = None,
        document_ids: list[str] | None = None,
    ) -> dict:
        session = UUID(session_id)
        conversation = (
            await self._chat.get_conversation(UUID(conversation_id), session)
            if conversation_id
            else await self._chat.start_conversation(session)
        )
        message, answer = await self._chat.ask(
            conversation.id,
            session,
            question,
            [UUID(document_id) for document_id in document_ids] if document_ids else None,
        )
        return {
            "conversation_id": str(conversation.id),
            "message_id": str(message.id),
            "result": answer.model_dump(mode="json"),
        }

    async def get_conversation(self, session_id: str, conversation_id: str) -> dict:
        session = UUID(session_id)
        conversation = await self._chat.get_conversation(UUID(conversation_id), session)
        messages = await self._chat.list_messages(conversation.id, session)
        return {
            "conversation": conversation.model_dump(mode="json"),
            "messages": messages,
        }
