'use client';

import { createClient, Session } from '@supabase/supabase-js';
import { useCallback, useEffect, useMemo, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
const USERS = [
  ['00000000-0000-0000-0000-000000000001', 'Avery'],
  ['00000000-0000-0000-0000-000000000002', 'Blake'],
] as const;

type Approval = { id: string; reason: string; risk_flags: string[]; status: string };
type Event = { id: string; agent: string; output_summary: string; duration_ms: number };
type Source = { title: string; url: string; snippet: string; published_date?: string };
type Memory = { id: string; content: string; source_task_id?: string; expires_at: string };
type Task = {
  id: string;
  title: string;
  input: string;
  status: string;
  current_node: string;
  result?: string;
  error?: string;
  approval?: Approval;
  events?: Event[];
  sources?: Source[];
  risk_flags?: string[];
};

const ACTIVE_STATUSES = new Set(['in_progress', 'awaiting_approval']);

export default function Page() {
  const supabase = useMemo(
    () => (SUPABASE_URL && SUPABASE_KEY ? createClient(SUPABASE_URL, SUPABASE_KEY) : null),
    [],
  );
  const [session, setSession] = useState<Session | null>(null);
  const [email, setEmail] = useState('');
  const [notice, setNotice] = useState('');
  const [user, setUser] = useState(USERS[0][0]);
  const [input, setInput] = useState('Compare three workflow tools in a table');
  const [remember, setRemember] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [task, setTask] = useState<Task>();
  const [memories, setMemories] = useState<Memory[]>([]);
  const [busy, setBusy] = useState(false);
  const [loadingWorkspace, setLoadingWorkspace] = useState(false);

  useEffect(() => {
    if (!supabase) return;
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data } = supabase.auth.onAuthStateChange((_event, next) => setSession(next));
    return () => data.subscription.unsubscribe();
  }, [supabase]);

  const authHeaders = useCallback((json = false): HeadersInit => {
    const headers: Record<string, string> = {};
    if (json) headers['content-type'] = 'application/json';
    if (session?.access_token) headers.authorization = `Bearer ${session.access_token}`;
    else headers['X-Demo-User-Id'] = user;
    return headers;
  }, [session, user]);

  const request = useCallback(async (path: string, init: RequestInit = {}) => {
    const response = await fetch(`${API}${path}`, init);
    const body = response.status === 204 ? null : await response.json();
    if (!response.ok) throw new Error(body?.detail?.code || 'request_failed');
    return body;
  }, []);

  const loadTask = useCallback(async (taskId: string) => {
    const detail = await request(`/api/tasks/${taskId}`, { headers: authHeaders() });
    setTask(detail);
    return detail as Task;
  }, [authHeaders, request]);

  const refreshWorkspace = useCallback(async (preferredTaskId?: string) => {
    if (supabase && !session) return;
    setLoadingWorkspace(true);
    setNotice('');
    try {
      const [nextTasks, nextMemories] = await Promise.all([
        request('/api/tasks', { headers: authHeaders() }),
        request('/api/memories', { headers: authHeaders() }),
      ]);
      setTasks(nextTasks);
      setMemories(nextMemories);
      const selected = preferredTaskId || task?.id || nextTasks[0]?.id;
      if (selected) await loadTask(selected);
      else setTask(undefined);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'workspace_unavailable');
    } finally {
      setLoadingWorkspace(false);
    }
  }, [authHeaders, loadTask, request, session, supabase, task?.id]);

  useEffect(() => {
    void refreshWorkspace();
    // Reconnect whenever the verified identity changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session?.access_token, user]);

  useEffect(() => {
    if (!task || !ACTIVE_STATUSES.has(task.status)) return;
    const timer = window.setInterval(() => void loadTask(task.id), 2500);
    return () => window.clearInterval(timer);
  }, [loadTask, task]);

  async function sendMagicLink() {
    if (!supabase || !email) return;
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: window.location.origin },
    });
    setNotice(error ? error.message : 'Check your email for the secure sign-in link.');
  }

  async function startGraph() {
    setBusy(true);
    setNotice('');
    try {
      const created = await request('/api/tasks', {
        method: 'POST',
        headers: authHeaders(true),
        body: JSON.stringify({ title: 'Research brief', input, remember }),
      });
      await refreshWorkspace(created.id);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'request_failed');
    } finally {
      setBusy(false);
    }
  }

  async function act(path: string, body?: object) {
    if (!task) return;
    setBusy(true);
    setNotice('');
    try {
      await request(path, {
        method: 'POST',
        headers: authHeaders(Boolean(body)),
        body: body ? JSON.stringify(body) : undefined,
      });
      await refreshWorkspace(task.id);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'request_failed');
    } finally {
      setBusy(false);
    }
  }

  async function decide(kind: 'approve' | 'reject') {
    if (!task?.approval) return;
    await act(`/api/approvals/${task.approval.id}/${kind}`, { note: `${kind}d in dashboard` });
  }

  async function deleteMemory(memoryId: string) {
    try {
      await request(`/api/memories/${memoryId}`, { method: 'DELETE', headers: authHeaders() });
      await refreshWorkspace(task?.id);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'request_failed');
    }
  }

  async function exportMemories() {
    try {
      const exported = await request('/api/memories/export', { headers: authHeaders() });
      const blob = new Blob([JSON.stringify(exported, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'stategraph-memories.json';
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'request_failed');
    }
  }

  const liveAuthRequired = Boolean(supabase && !session);

  return <main>
    <nav aria-label="Product"><b>STATEGRAPH</b><span>Bounded autonomy, visible state.</span></nav>
    <header>
      <small>MULTI-AGENT ORCHESTRATOR</small>
      <h1>Agents that pause<br/><i>before they overstep.</i></h1>
      <p>Four typed agents. Durable checkpoints. Per-user memory. A real human veto.</p>
    </header>

    <section className="panel composer" aria-labelledby="new-task-heading">
      <h2 id="new-task-heading">Start a governed run</h2>
      {supabase ? (
        session ? <div className="identity">
          <span>Signed in as {session.user.email}</span>
          <button className="ghost" onClick={() => supabase.auth.signOut()}>Sign out</button>
        </div> : <div className="identity">
          <label>Email<input type="email" value={email} onChange={event => setEmail(event.target.value)} /></label>
          <button onClick={sendMagicLink}>Send secure sign-in link</button>
        </div>
      ) : (
        <label>Local demo identity
          <select value={user} onChange={event => setUser(event.target.value as typeof user)}>
            {USERS.map(option => <option key={option[0]} value={option[0]}>{option[1]}</option>)}
          </select>
        </label>
      )}
      <label>Research task<textarea value={input} onChange={event => setInput(event.target.value)} /></label>
      <label className="remember"><input type="checkbox" checked={remember} onChange={event => setRemember(event.target.checked)} /> Save one explicit preference memory from this task</label>
      <button onClick={startGraph} disabled={busy || liveAuthRequired || input.trim().length < 8}>{busy ? 'Working…' : 'Start graph →'}</button>
      {notice && <p className="notice" role="status">{notice.replaceAll('_', ' ')}</p>}
    </section>

    <section className="workspace" aria-label="Run workspace">
      <aside className="sidebar">
        <div className="sectionTitle"><h2>Runs</h2><button className="textButton" onClick={() => refreshWorkspace()} disabled={loadingWorkspace}>Refresh</button></div>
        {tasks.length === 0 ? <p className="empty">No runs for this identity yet.</p> : tasks.map(item =>
          <button key={item.id} className={`taskRow ${task?.id === item.id ? 'selected' : ''}`} onClick={() => loadTask(item.id)}>
            <b>{item.title || 'Research brief'}</b><span>{item.status.replaceAll('_', ' ')}</span>
          </button>
        )}
      </aside>

      <div className="runDetail">
        {!task ? <div className="emptyState"><h2>Select or start a run</h2><p>Its checkpoint, evidence and approval state will appear here.</p></div> : <>
          <div className="runHeading">
            <div><span className={`status ${task.status}`}>{task.status.replaceAll('_', ' ')}</span><h2>Checkpoint: {task.current_node}</h2></div>
            <div className="actions">
              {task.status === 'failed' && <button onClick={() => act(`/api/tasks/${task.id}/resume`)}>Retry checkpoint</button>}
              {ACTIVE_STATUSES.has(task.status) && <button className="ghost" onClick={() => act(`/api/tasks/${task.id}/cancel`)}>Cancel</button>}
            </div>
          </div>
          {task.error && <div className="error" role="alert">A dependency is unavailable. Your checkpoint is safe; retry when ready.</div>}
          {task.status === 'awaiting_approval' && task.approval && <div className="approval">
            <b>Human approval required</b><p>{task.approval.reason}</p>
            <ul>{task.approval.risk_flags.map(flag => <li key={flag}>{flag.replaceAll('_', ' ')}</li>)}</ul>
            <button onClick={() => decide('approve')} disabled={busy}>Approve &amp; resume</button>
            <button className="ghost" onClick={() => decide('reject')} disabled={busy}>Reject</button>
          </div>}

          <div className="detailGrid">
            <section><h3>Timeline</h3>{task.events?.length ? <ol className="timeline">{task.events.map(event =>
              <li key={event.id}><b>{event.agent}</b><p>{event.output_summary}</p><small>{event.duration_ms} ms</small></li>
            )}</ol> : <p className="empty">Waiting for the first completed node.</p>}</section>
            <section><h3>Evidence</h3>{task.sources?.length ? <div className="sources">{task.sources.map(source =>
              <a key={source.url} href={source.url} target="_blank" rel="noreferrer"><b>{source.title}</b><p>{source.snippet}</p><span>{new URL(source.url).hostname} ↗</span></a>
            )}</div> : <p className="empty">No validated sources available yet.</p>}</section>
          </div>
          {task.result && <section className="result"><h3>Final deliverable</h3><pre>{task.result}</pre></section>}
        </>}
      </div>
    </section>

    <section className="memoryPanel" aria-labelledby="memory-heading">
      <div className="sectionTitle"><div><small>USER CONTROLLED</small><h2 id="memory-heading">Memory manager</h2></div><button className="textButton" onClick={exportMemories} disabled={!memories.length}>Export JSON</button></div>
      {memories.length === 0 ? <p className="empty">No saved memories. Memory is off unless you opt in on a task.</p> : <div className="memoryList">{memories.map(memory =>
        <article key={memory.id}><div><b>{memory.content}</b><p>Expires {new Date(memory.expires_at).toLocaleDateString()}</p></div><button className="danger" onClick={() => deleteMemory(memory.id)}>Delete</button></article>
      )}</div>}
    </section>

    <section className="grid" aria-label="Graph stages">{['Research', 'Analyst', 'Reviewer', 'Human gate', 'Writer'].map(item => <div key={item}>{item}</div>)}</section>
    <footer>Local mode uses explicit demo identities. Live mode verifies Supabase JWTs and database RLS at every projection boundary.</footer>
  </main>;
}
