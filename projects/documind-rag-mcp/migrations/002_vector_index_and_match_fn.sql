-- DocuMind migration 002: HNSW index + similarity search function (idempotent)
--
-- HNSW over IVFFlat: the demo corpus is small and grows incrementally.
-- IVFFlat requires training data at index build time and degrades when rows
-- are inserted after the lists were computed; HNSW builds incrementally and
-- gives better recall at small scale. Tradeoff (documented in DECISIONS.md):
-- HNSW uses more memory per row — irrelevant at demo scale.

create index if not exists idx_chunks_embedding_hnsw
  on document_chunks
  using hnsw (embedding vector_cosine_ops)
  with (m = 16, ef_construction = 64);

-- Similarity search with threshold + optional document filter.
-- Cosine distance operator <=> returns distance in [0, 2]; similarity = 1 - distance.
create or replace function match_document_chunks(
  query_embedding vector(768),
  match_count integer default 8,
  similarity_threshold double precision default 0.35,
  filter_document_ids uuid[] default null,
  filter_session_id uuid default null
)
returns table (
  chunk_id uuid,
  document_id uuid,
  page_number integer,
  chunk_index integer,
  content text,
  similarity double precision
)
language sql
stable
as $$
  select
    dc.id as chunk_id,
    dc.document_id,
    dc.page_number,
    dc.chunk_index,
    dc.content,
    1 - (dc.embedding <=> query_embedding) as similarity
  from document_chunks dc
  join documents d on d.id = dc.document_id
  where dc.embedding is not null
    and d.status = 'ready'
    and (filter_session_id is null or d.session_id = filter_session_id)
    and (filter_document_ids is null or dc.document_id = any (filter_document_ids))
    and 1 - (dc.embedding <=> query_embedding) >= similarity_threshold
  order by dc.embedding <=> query_embedding
  limit match_count;
$$;
