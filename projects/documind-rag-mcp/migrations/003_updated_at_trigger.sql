-- DocuMind migration 003: keep documents.updated_at accurate (idempotent)

create or replace function set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_documents_updated_at on documents;
create trigger trg_documents_updated_at
  before update on documents
  for each row
  execute function set_updated_at();
