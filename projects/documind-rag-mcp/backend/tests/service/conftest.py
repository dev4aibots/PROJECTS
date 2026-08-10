"""Shared fixtures: fully wired services over memory repos + deterministic providers."""

import pytest

from app.providers.deterministic import (
    DeterministicChatProvider,
    DeterministicEmbeddingProvider,
)
from app.repositories.memory import (
    MemoryChunkRepository,
    MemoryConversationRepository,
    MemoryDocumentRepository,
    MemoryRetrievalLogRepository,
    MemoryStorageRepository,
)
from app.services.chat import ChatService
from app.services.documents import DocumentService


class World:
    """One fully wired application world per test."""

    def __init__(self, chat_provider=None) -> None:
        self.documents_repo = MemoryDocumentRepository()
        self.chunks_repo = MemoryChunkRepository(self.documents_repo)
        self.conversations_repo = MemoryConversationRepository()
        self.logs_repo = MemoryRetrievalLogRepository()
        self.storage_repo = MemoryStorageRepository()
        self.embeddings = DeterministicEmbeddingProvider(dimensions=256)
        self.chat_provider = chat_provider or DeterministicChatProvider()

        self.document_service = DocumentService(
            documents=self.documents_repo,
            chunks=self.chunks_repo,
            storage=self.storage_repo,
            embeddings=self.embeddings,
            pages_per_batch=2,
        )
        self.chat_service = ChatService(
            conversations=self.conversations_repo,
            chunks=self.chunks_repo,
            retrieval_logs=self.logs_repo,
            embeddings=self.embeddings,
            chat=self.chat_provider,
            similarity_threshold=0.05,  # hash embeddings are weak; keep gate real but reachable
        )


@pytest.fixture
def world() -> World:
    return World()
