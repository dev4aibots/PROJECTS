BEGIN;
CREATE TABLE IF NOT EXISTS documents(id uuid PRIMARY KEY,filename text NOT NULL,content_type text NOT NULL,file_size bigint NOT NULL,storage_path text,status text NOT NULL,error text,session_id text NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS invoices(id uuid PRIMARY KEY,document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,invoice_number text NOT NULL,vendor_name text NOT NULL,invoice_date date NOT NULL,currency text NOT NULL,subtotal numeric NOT NULL,tax numeric,total numeric NOT NULL,raw_extraction jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS invoice_items(id uuid PRIMARY KEY,invoice_id uuid NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,position integer NOT NULL,description text NOT NULL,quantity numeric NOT NULL,unit_price numeric NOT NULL,line_total numeric NOT NULL);
CREATE TABLE IF NOT EXISTS verification_results(id uuid PRIMARY KEY,invoice_id uuid NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,status text NOT NULL,checks jsonb NOT NULL,tolerance numeric NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
COMMIT;
