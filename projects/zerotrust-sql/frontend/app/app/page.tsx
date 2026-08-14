'use client';

import Link from 'next/link';
import {useCallback, useEffect, useMemo, useState} from 'react';

const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

type Check = {name: string; passed: boolean; detail: string};
type Result = {
  question: string;
  generated_sql: string | null;
  executed_sql: string | null;
  columns: string[];
  rows: (string | number | null)[][];
  row_count: number;
  explanation: string;
  security: {
    allowed: boolean;
    checks: Check[];
    rejection_reason: string | null;
    limit_injected?: boolean;
  };
};
type Attack = {id: number; label: string; question: string; expected: string};
type AuditEntry = {
  id: number;
  validation_status: string;
  question?: string | null;
  question_hash?: string | null;
  row_count?: number | null;
  model?: string | null;
};

async function responseJson(response: Response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.detail || `Request failed (${response.status})`);
    error.name = response.status === 429 ? 'RateLimitError' : 'ApiError';
    throw error;
  }
  return body;
}

export default function Workbench() {
  const [question, setQuestion] = useState('Top 10 customers by revenue');
  const [token, setToken] = useState('');
  const [result, setResult] = useState<Result | null>(null);
  const [attacks, setAttacks] = useState<Attack[]>([]);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [auditMessage, setAuditMessage] = useState('');

  const authenticatedHeaders = useMemo(() => {
    const headers: Record<string, string> = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    return headers;
  }, [token]);

  const refresh = useCallback(async () => {
    try {
      const attackResponse = await fetch(`${API}/api/attacks`, {cache: 'no-store'});
      const attackBody = await responseJson(attackResponse);
      setAttacks(attackBody.attacks);
    } catch {
      setError('API unavailable. Start the FastAPI service on port 8000.');
      return;
    }

    try {
      const auditResponse = await fetch(`${API}/api/audit?limit=20`, {
        headers: authenticatedHeaders,
        cache: 'no-store',
      });
      const auditBody = await responseJson(auditResponse);
      setAudit(auditBody.entries);
      setAuditMessage('');
    } catch (auditError) {
      setAudit([]);
      setAuditMessage(
        auditError instanceof Error && auditError.name === 'ApiError'
          ? 'Audit access requires an audit-scoped token.'
          : 'Audit history is temporarily unavailable.',
      );
    }
  }, [authenticatedHeaders]);

  useEffect(() => {
    setToken(window.sessionStorage.getItem('zerotrust-access-token') || '');
  }, []);

  useEffect(() => {
    if (token) window.sessionStorage.setItem('zerotrust-access-token', token);
    else window.sessionStorage.removeItem('zerotrust-access-token');
    void refresh();
  }, [refresh, token]);

  async function run(nextQuestion = question) {
    setQuestion(nextQuestion);
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API}/api/query`, {
        method: 'POST',
        headers: {'content-type': 'application/json', ...authenticatedHeaders},
        body: JSON.stringify({question: nextQuestion}),
      });
      setResult(await responseJson(response));
      await refresh();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Request failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <nav><Link href="/">← Overview</Link><b>SECURE ANALYTICS WORKBENCH</b></nav>
      <header>
        <p className="eyebrow">LIVE PIPELINE INSPECTION</p>
        <h1>Ask. Inspect. <em>Trust nothing.</em></h1>
      </header>
      <section className="panel access-panel">
        <div>
          <label htmlFor="access-token">Access token</label>
          <p>Leave blank in deterministic local mode. Live tokens stay in this browser tab only.</p>
        </div>
        <input
          id="access-token"
          type="password"
          autoComplete="off"
          value={token}
          onChange={(event) => setToken(event.target.value)}
          placeholder="Bearer token"
        />
      </section>
      <div className="workbench">
        <section className="panel mainpanel">
          <label htmlFor="question">Business question</label>
          <div className="ask">
            <textarea
              id="question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              maxLength={500}
            />
            <button onClick={() => void run()} disabled={loading}>
              {loading ? 'Validating…' : 'Generate + validate'}
            </button>
          </div>
          {error && <p className="error" role="alert">{error}</p>}
          {!result && !error && <p className="empty">Run a question to inspect generated SQL and every security verdict.</p>}
          {result && <>
            <div className={`verdict ${result.security.allowed ? 'allowed' : 'blocked'}`}>
              <b>{result.security.allowed ? 'ALLOWED' : 'BLOCKED'}</b>
              <span>{result.security.rejection_reason || `${result.row_count} rows returned`}</span>
              {result.security.limit_injected && <mark>LIMIT INJECTED</mark>}
            </div>
            <h3>Generated SQL</h3>
            <pre>{result.generated_sql}</pre>
            <h3>Security report</h3>
            <div className="checks">
              {result.security.checks.map((check) => <div key={check.name} className={check.passed ? 'pass' : 'fail'}>
                <b>{check.passed ? 'PASS' : 'FAIL'} · {check.name}</b><span>{check.detail}</span>
              </div>)}
            </div>
            <p>{result.explanation}</p>
            {result.columns.length > 0 && <div className="tablewrap"><table>
              <thead><tr>{result.columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
              <tbody>{result.rows.map((row, rowIndex) => <tr key={rowIndex}>
                {row.map((value, columnIndex) => <td key={columnIndex}>{String(value ?? '')}</td>)}
              </tr>)}</tbody>
            </table></div>}
          </>}
        </section>
        <aside className="panel">
          <h2>Attack lab</h2><p>One click submits the actual hostile prompt.</p>
          {attacks.map((attack) => <button className="attack" key={attack.id} onClick={() => void run(attack.question)}>
            <small>ATTACK {String(attack.id).padStart(2, '0')}</small>
            <b>{attack.label}</b><span>{attack.expected}</span>
          </button>)}
        </aside>
      </div>
      <section className="panel">
        <h2>Recent audit events</h2>
        {auditMessage && <p className="empty">{auditMessage}</p>}
        {!auditMessage && audit.length === 0 && <p className="empty">No requests recorded yet.</p>}
        {audit.length > 0 && <div className="tablewrap"><table>
          <thead><tr><th>ID</th><th>Status</th><th>Question / hash</th><th>Rows</th><th>Model</th></tr></thead>
          <tbody>{audit.map((entry) => <tr key={entry.id}>
            <td>{entry.id}</td><td>{entry.validation_status}</td>
            <td>{entry.question || (entry.question_hash ? `${entry.question_hash.slice(0, 16)}…` : '—')}</td>
            <td>{entry.row_count ?? '—'}</td><td>{entry.model ?? '—'}</td>
          </tr>)}</tbody>
        </table></div>}
      </section>
    </main>
  );
}
