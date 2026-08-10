-- DocuMind migration 005: preserve self-contained citations after chunk deletion.
-- Migration 004 made chunk_id nullable; this migration replaces the original
-- cascading foreign key with ON DELETE SET NULL. It is safe to rerun.

do $$
declare
  constraint_name text;
begin
  select tc.constraint_name
    into constraint_name
  from information_schema.table_constraints tc
  join information_schema.key_column_usage kcu
    on tc.constraint_name = kcu.constraint_name
   and tc.constraint_schema = kcu.constraint_schema
  where tc.table_schema = 'public'
    and tc.table_name = 'message_citations'
    and tc.constraint_type = 'FOREIGN KEY'
    and kcu.column_name = 'chunk_id'
  limit 1;

  if constraint_name is not null then
    execute format('alter table message_citations drop constraint %I', constraint_name);
  end if;

  if not exists (
    select 1
    from information_schema.table_constraints
    where table_schema = 'public'
      and table_name = 'message_citations'
      and constraint_name = 'message_citations_chunk_id_fkey'
  ) then
    alter table message_citations
      add constraint message_citations_chunk_id_fkey
      foreign key (chunk_id) references document_chunks (id) on delete set null;
  end if;
end
$$;
