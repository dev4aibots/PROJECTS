"""Application settings loaded from environment variables.

Every value has a safe default for local, secret-free test runs. Live
integrations (Supabase, Groq, Gemini, Langfuse) activate only when their
credentials are present.
"""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel, Field


class Settings(BaseModel):
    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "documents"

    # Providers
    groq_api_key: str = ""
    gemini_api_key: str = ""
    llm_provider: str = "groq"  # groq | gemini
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_model: str = "gemini-2.0-flash"
    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 768

    # Langfuse (optional; tracing must never break the primary path)
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    frontend_origin: str = ""

    # RAG configuration
    similarity_threshold: float = Field(default=0.35, ge=0.0, le=1.0)
    retrieval_top_k: int = Field(default=8, ge=1, le=50)
    chunk_target_tokens: int = Field(default=800, ge=100, le=2000)
    chunk_overlap_ratio: float = Field(default=0.15, ge=0.0, le=0.5)
    context_token_cap: int = Field(default=4000, ge=500, le=16000)

    # Upload constraints
    max_upload_bytes: int = 10 * 1024 * 1024
    process_pages_per_batch: int = Field(default=3, ge=1, le=20)

    # Input validation
    max_question_chars: int = 2000


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        supabase_url=_env("SUPABASE_URL"),
        supabase_service_role_key=_env("SUPABASE_SERVICE_ROLE_KEY"),
        supabase_storage_bucket=_env("SUPABASE_STORAGE_BUCKET", "documents"),
        groq_api_key=_env("GROQ_API_KEY"),
        gemini_api_key=_env("GEMINI_API_KEY"),
        llm_provider=_env("LLM_PROVIDER", "groq"),
        groq_model=_env("GROQ_MODEL", "llama-3.3-70b-versatile"),
        gemini_model=_env("GEMINI_MODEL", "gemini-2.0-flash"),
        embedding_model=_env("EMBEDDING_MODEL", "gemini-embedding-001"),
        embedding_dimensions=int(_env("EMBEDDING_DIMENSIONS", "768")),
        langfuse_public_key=_env("LANGFUSE_PUBLIC_KEY"),
        langfuse_secret_key=_env("LANGFUSE_SECRET_KEY"),
        langfuse_host=_env("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        frontend_origin=_env("FRONTEND_ORIGIN"),
        similarity_threshold=float(_env("SIMILARITY_THRESHOLD", "0.35")),
        retrieval_top_k=int(_env("RETRIEVAL_TOP_K", "8")),
        chunk_target_tokens=int(_env("CHUNK_TARGET_TOKENS", "800")),
        chunk_overlap_ratio=float(_env("CHUNK_OVERLAP_RATIO", "0.15")),
        context_token_cap=int(_env("CONTEXT_TOKEN_CAP", "4000")),
        process_pages_per_batch=int(_env("PROCESS_PAGES_PER_BATCH", "3")),
    )


def reset_settings_cache() -> None:
    """Test helper: clear cached settings after monkeypatching env vars."""
    get_settings.cache_clear()
