'use client';

import { createClient, Session } from '@supabase/supabase-js';
import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
const USERS = [
  ['00000000-0000-0000-0000-000000000001', 'Avery'],
  ['00000000-0000-0000-0000-000000000002', 'Blake'],
] as const;

type Check = { name: string; field: string; expected: string; actual: string; passed: boolean; delta: string };
type Invoice = {
  invoice_number: string;
  vendor_name: string;
  invoice_date: string;
  currency: string;
  subtotal: string;
  tax?: string;
  total: string;
  line_items: Array<{ description: string; quantity: string; unit_price: string; line_total: string }>;
};
type Document = {
  id: string;
  filename: string;
  content_type: string;
  file_size: number;
  status: string;
  error?: string;
  invoice?: Invoice;
  verification?: { status: string; checks: Check[]; tolerance: string };
  trust_labels?: Record<string, string>;
  possible_duplicate?: boolean;
  raw_extraction?: unknown;
  provider_model?: string;
};

export default function App() {
  const supabase = useMemo(
    () => (SUPABASE_URL && SUPABASE_KEY ? createClient(SUPABASE_URL, SUPABASE_KEY) : null),
    [],
  );
  const [session, setSession] = useState<Session | null>(null);
  const [email, setEmail] = useState('');
  const [user, setUser] = useState(USERS[0][0]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [document, setDocument] = useState<Document | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    if (!supabase) return;
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data } = supabase.auth.onAuthStateChange((_event, next) => setSession(next));
    return () => data.subscription.unsubscribe();
  }, [supabase]);

  const authHeaders = useCallback((): HeadersInit => {
    if (session?.access_token) return { Authorization: `Bearer ${session.access_token}` };
    return { 'X-Demo-User-Id': user };
  }, [session, user]);

  const parseResponse = useCallback(async (response: Response) => {
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = typeof body.detail === 'string' ? body.detail : body.detail?.code;
      throw new Error(detail || 'request_failed');
    }
    return body;
  }, []);

  const loadDocuments = useCallback(async (preferred?: string) => {
    if (supabase && !session) return;
    const response = await fetch(`${API}/api/documents`, { headers: authHeaders() });
    const body = await parseResponse(response) as { documents: Document[] };
    setDocuments(body.documents);
    const selected = preferred || document?.id || body.documents[0]?.id;
    if (!selected) {
      setDocument(null);
      return;
    }
    const detail = await fetch(`${API}/api/documents/${selected}`, { headers: authHeaders() });
    if (detail.status === 404) {
      setDocument(body.documents[0] || null);
      return;
    }
    setDocument(await parseResponse(detail) as Document);
  }, [authHeaders, document?.id, parseResponse, session, supabase]);

  useEffect(() => {
    setError('');
    setDocuments([]);
    setDocument(null);
    void loadDocuments().catch(() => setError('Workspace is temporarily unavailable.'));
    // Clear prior owner data immediately, then reconnect with the new verified identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session?.access_token, user]);

  async function sendMagicLink() {
    if (!supabase || !email.trim()) return;
    const { error: authError } = await supabase.auth.signInWithOtp({
      email: email.trim(),
      options: { emailRedirectTo: window.location.origin + '/app' },
    });
    setNotice(authError ? authError.message : 'Check your email for the secure sign-in link.');
  }

  async function processDocument(documentId: string) {
    const response = await fetch(`${API}/api/documents/${documentId}/process`, {
      method: 'POST',
      headers: authHeaders(),
    });
    return parseResponse(response) as Promise<Document>;
  }

  async function send(file: File) {
    setBusy(true);
    setError('');
    setNotice('');
    let uploadedId = '';
    try {
      const form = new FormData();
      form.append('file', file);
      const upload = await fetch(`${API}/api/documents/upload`, {
        method: 'POST',
        headers: authHeaders(),
        body: form,
      });
      const uploaded = await parseResponse(upload) as Document;
      uploadedId = uploaded.id;
      setDocument(uploaded);
      const processed = await processDocument(uploaded.id);
      setDocument(processed);
      await loadDocuments(processed.id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message.replaceAll('_', ' ') : 'Upload failed.');
      if (uploadedId) await loadDocuments(uploadedId).catch(() => undefined);
    } finally {
      setBusy(false);
    }
  }

  async function retry() {
    if (!document) return;
    setBusy(true);
    setError('');
    try {
      const processed = await processDocument(document.id);
      setDocument(processed);
      await loadDocuments(processed.id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message.replaceAll('_', ' ') : 'Retry failed.');
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!document) return;
    setBusy(true);
    try {
      const response = await fetch(`${API}/api/documents/${document.id}`, {
        method: 'DELETE',
        headers: authHeaders(),
      });
      await parseResponse(response);
      setDocument(null);
      await loadDocuments();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Delete failed.');
    } finally {
      setBusy(false);
    }
  }

  function exportJson() {
    if (!document) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(document, null, 2)], { type: 'application/json' }));
    const link = window.document.createElement('a');
    link.href = url;
    link.download = `${document.filename}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function sample(name: string) {
    const response = await fetch(`/samples/${name}`);
    const type = name.endsWith('.png') ? 'image/png' : 'application/pdf';
    await send(new File([await response.blob()], name, { type }));
  }

  const liveAuthRequired = Boolean(supabase && !session);
  const fields = ['invoice_date', 'currency', 'subtotal', 'tax', 'total'] as const;

  return <main>
    <nav><Link href="/">← Overview</Link><b>VERIFICATION CONSOLE</b></nav>
    <h1>Trust the math,<br/><em>not the model.</em></h1>

    <section className="card identity" aria-label="Identity">
      {supabase ? session ? <>
        <span>Signed in as {session.user.email}</span>
        <button onClick={() => supabase.auth.signOut()}>Sign out</button>
      </> : <>
        <label>Email <input type="email" value={email} onChange={event => setEmail(event.target.value)} /></label>
        <button onClick={sendMagicLink}>Send secure sign-in link</button>
      </> : <label>Local demo identity <select value={user} onChange={event => setUser(event.target.value as typeof user)}>
        {USERS.map(option => <option key={option[0]} value={option[0]}>{option[1]}</option>)}
      </select></label>}
      {notice && <p role="status">{notice}</p>}
    </section>

    <section className="card" aria-labelledby="upload-heading">
      <h2 id="upload-heading">Upload a private invoice</h2>
      <p>PDF up to 5 pages, PNG or JPEG. Maximum 8 MB. Provider values remain untrusted until arithmetic verification passes.</p>
      <input aria-label="Invoice file" disabled={busy || liveAuthRequired} type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={event => event.target.files?.[0] && send(event.target.files[0])}/>
      {!supabase && <div className="samples">{['clean_invoice.pdf', 'broken_total_invoice.pdf', 'broken_lineitem_invoice.pdf', 'receipt_photo.png', 'cat.png'].map(name =>
        <button disabled={busy} onClick={() => sample(name)} key={name}>{name}</button>
      )}</div>}
      {busy && <p role="status">Extracting and independently verifying…</p>}
      {error && <p className="bad" role="alert">{error}</p>}
    </section>

    <section className="workspace" aria-label="Document workspace">
      <aside className="card history">
        <div className="sectionTitle"><h2>Documents</h2><button onClick={() => loadDocuments()} disabled={busy || liveAuthRequired}>Refresh</button></div>
        {documents.length === 0 ? <p>No documents for this identity.</p> : documents.map(item =>
          <button className={document?.id === item.id ? 'selected' : ''} key={item.id} onClick={() => loadDocuments(item.id)}>
            <b>{item.filename}</b><span>{item.status.replaceAll('_', ' ')}</span>
          </button>
        )}
      </aside>

      <div className="documentDetail">
        {!document ? <section className="card empty"><h2>No document selected</h2><p>Upload an invoice or select one from your private history.</p></section> : <section className="card">
          <div className="sectionTitle"><div><small>{document.provider_model || 'awaiting provider'}</small><h2>{document.filename}</h2></div><div className="actions">
            {(document.status === 'uploaded' || document.status === 'failed_extraction') && <button onClick={retry} disabled={busy}>Retry</button>}
            <button onClick={exportJson}>Export JSON</button><button onClick={remove} disabled={busy}>Delete</button>
          </div></div>
          {document.possible_duplicate && <p className="warning">Possible duplicate invoice number for this owner.</p>}
          {document.status === 'failed_extraction' ? <div className="verdict bad"><b>FAILED_EXTRACTION</b><span>{document.error}</span></div> : document.invoice && document.verification ? <>
            <div className={`verdict ${document.verification.status === 'VERIFIED' ? 'good' : 'bad'}`}><b>{document.verification.status}</b><span>Invoice {document.invoice.invoice_number} · {document.invoice.vendor_name}</span></div>
            <div className="fields">{fields.map(field => <div key={field}><small>{field} · {document.trust_labels?.[field]}</small><strong>{document.invoice?.[field] ?? '—'}</strong></div>)}</div>
            <table><thead><tr><th>Description</th><th>Qty</th><th>Unit</th><th>Total</th></tr></thead><tbody>{document.invoice.line_items.map((item, index) => <tr key={`${item.description}-${index}`}><td>{item.description}</td><td>{item.quantity}</td><td>{item.unit_price}</td><td>{item.line_total}</td></tr>)}</tbody></table>
            <h3>Independent checks</h3>{document.verification.checks.map((check, index) => <div className={`check ${check.passed ? 'good' : 'bad'}`} key={`${check.name}-${index}`}><span>{check.name}</span><b>{check.passed ? 'PASS' : `FAIL · Δ ${check.delta}`}</b></div>)}
            <details><summary>Raw structured extraction</summary><pre>{JSON.stringify(document.raw_extraction, null, 2)}</pre></details>
          </> : <div className="verdict"><b>{document.status.replaceAll('_', ' ').toUpperCase()}</b><span>{document.error || 'Waiting for extraction.'}</span></div>}
        </section>}
      </div>
    </section>
  </main>;
}
