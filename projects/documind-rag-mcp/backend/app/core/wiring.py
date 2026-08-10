"""Application dependency wiring.

The default local mode is secret-free and deterministic. Live Supabase and
provider adapters activate only when all required credentials are present.
"""

from dataclasses import dataclass

from ..providers.deterministic import DeterministicChatProvider, DeterministicEmbeddingProvider
from ..providers.live import GeminiChatProvider, GeminiEmbeddingProvider, GroqChatProvider
from ..providers.resilient import ResilientChatProvider
from ..repositories.memory import (
    MemoryChunkRepository,
    MemoryConversationRepository,
    MemoryDocumentRepository,
    MemoryRetrievalLogRepository,
    MemoryStorageRepository,
)
from ..repositories.supabase import (
    SupabaseChunkRepository,
    SupabaseClient,
    SupabaseConversationRepository,
    SupabaseDocumentRepository,
    SupabaseRetrievalLogRepository,
    SupabaseStorageRepository,
)
from ..services.chat import ChatService
from ..services.documents import DocumentService
from .observability import LangfuseObserver, NoopObserver
from .settings import Settings, get_settings


@dataclass
class Container:
    document_service: DocumentService
    chat_service: ChatService
    retrieval_logs: object
    mode: str
    llm_mode: str


def build_container(settings: Settings | None = None) -> Container:
    settings = settings or get_settings()
    live_storage = bool(settings.supabase_url and settings.supabase_service_role_key)
    live_embeddings = bool(settings.gemini_api_key)

    if live_storage:
        client = SupabaseClient(settings)
        documents = SupabaseDocumentRepository(client)
        chunks = SupabaseChunkRepository(client)
        conversations = SupabaseConversationRepository(client)
        logs = SupabaseRetrievalLogRepository(client)
        storage = SupabaseStorageRepository(client)
        mode = "supabase"
    else:
        documents = MemoryDocumentRepository()
        chunks = MemoryChunkRepository(documents)
        conversations = MemoryConversationRepository()
        logs = MemoryRetrievalLogRepository()
        storage = MemoryStorageRepository()
        mode = "memory"

    embeddings = (
        GeminiEmbeddingProvider(
            settings.gemini_api_key,
            settings.embedding_model,
            settings.embedding_dimensions,
        )
        if live_embeddings
        else DeterministicEmbeddingProvider(settings.embedding_dimensions)
    )

    chat_providers = []
    if settings.llm_provider == "gemini" and settings.gemini_api_key:
        chat_providers.append(GeminiChatProvider(settings.gemini_api_key, settings.gemini_model))
    if settings.groq_api_key:
        chat_providers.append(GroqChatProvider(settings.groq_api_key, settings.groq_model))
    if settings.gemini_api_key and not any(getattr(p, "name", "") == "gemini" for p in chat_providers):
        chat_providers.append(GeminiChatProvider(settings.gemini_api_key, settings.gemini_model))

    if chat_providers:
        chat = ResilientChatProvider(chat_providers)
        llm_mode = "+".join(getattr(p, "name", "provider") for p in chat_providers)
    else:
        chat = DeterministicChatProvider()
        llm_mode = "deterministic"

    observer = (
        LangfuseObserver(
            settings.langfuse_public_key,
            settings.langfuse_secret_key,
            settings.langfuse_host,
        )
        if settings.langfuse_public_key and settings.langfuse_secret_key
        else NoopObserver()
    )

    document_service = DocumentService(
        documents,
        chunks,
        storage,
        embeddings,
        max_upload_bytes=settings.max_upload_bytes,
        pages_per_batch=settings.process_pages_per_batch,
        chunk_target_tokens=settings.chunk_target_tokens,
        chunk_overlap_ratio=settings.chunk_overlap_ratio,
    )
    chat_service = ChatService(
        conversations,
        chunks,
        logs,
        embeddings,
        chat,
        top_k=settings.retrieval_top_k,
        similarity_threshold=settings.similarity_threshold if live_embeddings else 0.05,
        context_token_cap=settings.context_token_cap,
        max_question_chars=settings.max_question_chars,
        observer=observer,
    )
    return Container(document_service, chat_service, logs, mode, llm_mode)
