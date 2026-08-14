BEGIN;

ALTER TABLE documents ADD COLUMN IF NOT EXISTS owner_id uuid;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS result jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS provider_model text;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS schema_version text;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS processing_version integer NOT NULL DEFAULT 0;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM documents WHERE owner_id IS NULL) THEN
    RAISE EXCEPTION 'documents.owner_id backfill is required before migration 002';
  END IF;
  IF EXISTS (SELECT 1 FROM documents WHERE storage_path IS NULL OR storage_path = '') THEN
    RAISE EXCEPTION 'documents.storage_path backfill is required before migration 002';
  END IF;
END $$;

ALTER TABLE documents ALTER COLUMN owner_id SET NOT NULL;
ALTER TABLE documents ALTER COLUMN storage_path SET NOT NULL;
ALTER TABLE documents DROP COLUMN IF EXISTS session_id;
ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_status_check;
ALTER TABLE documents ADD CONSTRAINT documents_status_check CHECK (
  status IN ('uploaded', 'processing', 'verified', 'verification_failed', 'failed_extraction')
);
CREATE INDEX IF NOT EXISTS documents_owner_created_idx
  ON documents(owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS invoices_number_idx ON invoices(invoice_number);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'docuextract_api') THEN
    CREATE ROLE docuextract_api NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
  END IF;
END $$;
GRANT docuextract_api TO CURRENT_USER;
GRANT USAGE ON SCHEMA public TO docuextract_api;
REVOKE ALL ON documents, invoices, invoice_items, verification_results FROM PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE
  ON documents, invoices, invoice_items, verification_results TO docuextract_api;

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents FORCE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices FORCE ROW LEVEL SECURITY;
ALTER TABLE invoice_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice_items FORCE ROW LEVEL SECURITY;
ALTER TABLE verification_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE verification_results FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS documents_owner_policy ON documents;
CREATE POLICY documents_owner_policy ON documents
  USING (owner_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid)
  WITH CHECK (owner_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid);

DROP POLICY IF EXISTS invoices_owner_policy ON invoices;
CREATE POLICY invoices_owner_policy ON invoices
  USING (EXISTS (
    SELECT 1 FROM documents d
    WHERE d.id = invoices.document_id
      AND d.owner_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM documents d
    WHERE d.id = invoices.document_id
      AND d.owner_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
  ));

DROP POLICY IF EXISTS invoice_items_owner_policy ON invoice_items;
CREATE POLICY invoice_items_owner_policy ON invoice_items
  USING (EXISTS (
    SELECT 1 FROM invoices i JOIN documents d ON d.id = i.document_id
    WHERE i.id = invoice_items.invoice_id
      AND d.owner_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM invoices i JOIN documents d ON d.id = i.document_id
    WHERE i.id = invoice_items.invoice_id
      AND d.owner_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
  ));

DROP POLICY IF EXISTS verification_results_owner_policy ON verification_results;
CREATE POLICY verification_results_owner_policy ON verification_results
  USING (EXISTS (
    SELECT 1 FROM invoices i JOIN documents d ON d.id = i.document_id
    WHERE i.id = verification_results.invoice_id
      AND d.owner_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM invoices i JOIN documents d ON d.id = i.document_id
    WHERE i.id = verification_results.invoice_id
      AND d.owner_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
  ));

COMMIT;
