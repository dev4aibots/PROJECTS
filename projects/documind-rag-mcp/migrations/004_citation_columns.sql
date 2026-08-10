-- DocuMind migration 004: persist self-contained validated citations (idempotent)
-- Chat history keeps its source label even if the source document is later deleted.

alter table message_citations
  add column if not exists document_id uuid,
  add column if not exists filename text not null default '';

alter table message_citations
  alter column chunk_id drop not null;

alter table message_citations
  add column if not exists page_number integer,
  add column if not exists excerpt text;
