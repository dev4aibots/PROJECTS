-- DocuMind migration 001: extensions and core tables (idempotent)
-- Run in Supabase SQL editor. Safe to re-run.

create extension if not exists vector;
create extension if not exists pgcrypto;

-- Document lifecycle status
do $$
begin
  if not exists (select 1 from pg_type where typname = 'document_status') then
    create type document_status as enum ('uploaded', 'processing', 'ready', 'failed');
  end if;
end
$$;

create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  filename text not null,
  content_type text not null,
  file_size integer not null check (file_size > 0 and file_size <= 10485760),
  storage_path text not null,
  status document_status not null default 'uploaded',
  page_count integer,
  last_processed_page integer not null default 0,
  processing_error text,
  session_id uuid not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_documents_session on documents (session_id);

create table if not exists document_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references documents (id) on delete cascade,
  page_number integer not null check (page_number >= 1),
  chunk_index integer not null check (chunk_index >= 0),
  content text not null,
  token_count integer not null,
  embedding vector(768),
  created_at timestamptz not null default now(),
  -- Idempotency key: reprocessing a page can never create duplicates.
  constraint uq_chunk_position unique (document_id, page_number, chunk_index)
);

create index if not exists idx_chunks_document on document_chunks (document_id);

create table if not exists conversations (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null,
  title text,
  created_at timestamptz not null default now()
);

create index if not exists idx_conversations_session on conversations (session_id);

create table if not exists messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references conversations (id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  grounded boolean,
  confidence double precision,
  created_at timestamptz not null default now()
);

create index if not exists idx_messages_conversation on messages (conversation_id);

create table if not exists message_citations (
  id uuid primary key default gen_random_uuid(),
  message_id uuid not null references messages (id) on delete cascade,
  chunk_id uuid not null references document_chunks (id) on delete cascade,
  page_number integer not null,
  excerpt text not null
);

create index if not exists idx_citations_message on message_citations (message_id);

create table if not exists retrieval_logs (
  id uuid primary key default gen_random_uuid(),
  message_id uuid references messages (id) on delete cascade,
  query text not null,
  top_k integer not null,
  threshold double precision not null,
  returned_count integer not null,
  max_similarity double precision,
  duration_ms integer not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_retrieval_logs_message on retrieval_logs (message_id);
