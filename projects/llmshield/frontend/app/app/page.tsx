'use client';

import Link from 'next/link';
import { FormEvent, useCallback, useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

type Verdict = 'PASS' | 'WARN' | 'BLOCK';
type Check = { name: string; verdict: Verdict; detail: string; stage: 'input' | 'output' };
type GatewayResult = {
  answer: string | null;
  security_status: 'safe' | 'warned' | 'blocked' | 'error';
  checks: Check[];
  provider: string | null;
  fallback_used: boolean;
  latency_ms: number;
  trace_id: string;
  truncated: boolean;
  error_code?: string | null;
};
type Stats = { total: number; blocked_pct: number; fallback_pct: number; p95_latency_ms: number };
type Attack = { label: string; prompt: string };
type Log = { id: string; prompt_sha256: string; security_status: string; provider: string | null; fallback_used: boolean; latency_ms: number };

async function readJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, init);
  const body = (await response.json()) as T & { detail?: unknown };
  if (!response.ok && path !== '/api/gateway') throw new Error(`Request failed (${response.status})`);
  return body;
}

export default function AttackConsole() {
  const [prompt, setPrompt] = useState('Explain zero trust in one sentence.');
  const [result, setResult] = useState<GatewayResult | null>(null);
  const [attacks, setAttacks] = useState<Attack[]>([]);
  const [stats, setStats] = useState<Stats>({ total: 0, blocked_pct: 0, fallback_pct: 0, p95_latency_ms: 0 });
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [telemetryError, setTelemetryError] = useState('');
  const [gatewayToken, setGatewayToken] = useState('');
  const [telemetryToken, setTelemetryToken] = useState('');

  const authorization = (token: string): HeadersInit => token ? { Authorization: `Bearer ${token}` } : {};

  const refresh = useCallback(async () => {
    setTelemetryError('');
    const headers = authorization(telemetryToken);
    const [nextStats, nextLogs] = await Promise.all([
      readJson<Stats>('/api/stats', { headers }),
      readJson<{ logs: Log[] }>('/api/logs?limit=8', { headers }),
    ]);
    setStats(nextStats);
    setLogs(nextLogs.logs);
  }, [telemetryToken]);

  useEffect(() => {
    readJson<{ attacks: Attack[] }>('/api/attacks')
      .then((attackData) => setAttacks(attackData.attacks))
      .catch(() => setError('The gateway is unavailable. Start the API or verify NEXT_PUBLIC_API_BASE_URL.'));
    refresh().catch(() => setTelemetryError('Private telemetry is locked. Enter a telemetry-scoped token to load it.'));
  }, [refresh]);

  async function run(nextPrompt = prompt) {
    if (loading) return;
    setPrompt(nextPrompt);
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const body = await readJson<GatewayResult>('/api/gateway', {
        method: 'POST',
        headers: { 'content-type': 'application/json', ...authorization(gatewayToken) },
        body: JSON.stringify({ prompt: nextPrompt }),
      });
      setResult(body);
      await refresh().catch(() => setTelemetryError('Request completed, but private telemetry remains locked.'));
    } catch {
      setError('The request could not be completed. Check the API health endpoint and try again.');
    } finally {
      setLoading(false);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void run();
  }

  const statCards: Array<[string, string | number]> = [
    ['Requests', stats.total],
    ['Blocked', `${stats.blocked_pct}%`],
    ['Fallback', `${stats.fallback_pct}%`],
    ['p95 latency', `${stats.p95_latency_ms} ms`],
  ];

  return (
    <main>
      <nav><Link href="/">← Home</Link><b>ATTACK CONSOLE</b></nav>
      <aside>Heuristic guards — defense in depth, not a guarantee.</aside>

      <section className="credentials" aria-labelledby="access-heading">
        <div className="resultHeading"><h2 id="access-heading">Scoped access</h2><small>Tokens stay in memory and are never persisted by this page.</small></div>
        <div className="credentialGrid">
          <label>Gateway token<input type="password" autoComplete="off" value={gatewayToken} onChange={(event) => setGatewayToken(event.target.value)} placeholder="Optional in local mode" /></label>
          <label>Telemetry token<input type="password" autoComplete="off" value={telemetryToken} onChange={(event) => setTelemetryToken(event.target.value)} placeholder="Required for private logs/stats" /></label>
        </div>
        <button type="button" className="secondary" onClick={() => refresh().catch(() => setTelemetryError('The telemetry token was rejected.'))}>Unlock telemetry</button>
      </section>

      {telemetryError && <p className="notice" role="status">{telemetryError}</p>}
      <div className="stats">
        {statCards.map(([label, value]) => <div key={label}><small>{label}</small><b>{value}</b></div>)}
      </div>

      <form onSubmit={submit}>
        <label htmlFor="prompt">Prompt</label>
        <textarea id="prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} maxLength={8001} />
        <div className="actions">
          <button type="submit" disabled={loading}>{loading ? 'Inspecting…' : 'Send through gateway'}</button>
          {attacks.map((attack) => <button type="button" className="secondary" key={attack.label} onClick={() => void run(attack.prompt)} disabled={loading}>{attack.label}</button>)}
        </div>
      </form>

      {error && <p className="error" role="alert">{error}</p>}
      {!result && !loading && !error && <p className="empty">Choose a demo or send a prompt to inspect every gateway stage.</p>}
      {loading && <p className="empty" aria-live="polite">Running input guards, provider routing, and output guards…</p>}

      {result && (
        <section className="result" aria-live="polite">
          <div className="resultHeading"><h2>{result.security_status}</h2><span>{result.error_code || (result.fallback_used ? 'fallback used' : 'primary path')}</span></div>
          <p>{result.answer || 'No answer was released.'}{result.truncated ? ' [truncated]' : ''}</p>
          <h3>Security checks</h3>
          {result.checks.map((check) => (
            <div className={`check ${check.verdict}`} key={`${check.stage}-${check.name}`}>
              <b>{check.verdict} · {check.name}</b><span>{check.detail}</span>
            </div>
          ))}
          <small>trace {result.trace_id} · provider {result.provider || 'none'} · {result.latency_ms} ms</small>
        </section>
      )}

      <section className="history">
        <div className="resultHeading"><h2>Privacy-safe history</h2><small>SHA-256 only; prompts are not stored</small></div>
        {logs.length === 0 ? <p className="empty">No requests in this process yet.</p> : (
          <div className="tableWrap"><table><thead><tr><th>Prompt hash</th><th>Status</th><th>Provider</th><th>Latency</th></tr></thead><tbody>
            {logs.map((log) => <tr key={log.id}><td><code>{log.prompt_sha256.slice(0, 14)}…</code></td><td>{log.security_status}</td><td>{log.provider || 'none'}{log.fallback_used ? ' (fallback)' : ''}</td><td>{log.latency_ms} ms</td></tr>)}
          </tbody></table></div>
        )}
      </section>
    </main>
  );
}
