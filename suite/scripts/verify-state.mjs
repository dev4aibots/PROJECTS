import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { dirname, resolve, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

export function validateTasks(state) {
  const errors = [];
  const tasks = state.tasks ?? [];
  const ids = new Set(tasks.map(t => t.id));
  const statuses = new Set(['planned', 'in_progress', 'blocked', 'verified']);
  if (state.version !== 1 || !tasks.length) errors.push('Invalid version or empty task graph');
  if (ids.size !== tasks.length) errors.push('Duplicate task IDs');
  const active = tasks.filter(t => ['in_progress', 'blocked'].includes(t.status));
  if (active.length !== 1 || active[0]?.id !== state.active_task) errors.push('Exactly one active task must match active_task');
  for (const t of tasks) {
    if (!statuses.has(t.status)) errors.push(`${t.id}: invalid status`);
    if (!Array.isArray(t.depends_on) || !Array.isArray(t.evidence)) { errors.push(`${t.id}: missing arrays`); continue; }
    if (t.status === 'verified' && !t.evidence.length) errors.push(`${t.id}: verified without evidence`);
    for (const id of t.depends_on) {
      const dependency = tasks.find(d => d.id === id);
      if (!dependency) errors.push(`${t.id}: unknown dependency ${id}`);
      if (t.status !== 'planned' && dependency?.status !== 'verified') errors.push(`${t.id}: prerequisite ${id} not verified`);
    }
  }
  const visited = new Set(), visiting = new Set();
  function visit(id) {
    if (visiting.has(id)) { errors.push(`Cycle at ${id}`); return; }
    if (visited.has(id)) return;
    visiting.add(id);
    for (const dep of tasks.find(t => t.id === id)?.depends_on ?? []) if (ids.has(dep)) visit(dep);
    visiting.delete(id); visited.add(id);
  }
  for (const id of ids) visit(id);
  return errors;
}

export function verifyRepository(root) {
  const errors = validateTasks(JSON.parse(readFileSync(resolve(root, 'suite/STATUS.json'), 'utf8')));
  for (const old of ['projects', 'docs', 'vercel.json']) if (existsSync(resolve(root, old))) errors.push(`Removed legacy path restored: ${old}`);
  const expected = ['AGENT_PROTOCOL','HANDOFF','REQUIREMENTS','RESEARCH','ARCHITECTURE','DATABASE','DESIGN','SECURITY_TESTING','ROADMAP','DEPLOYMENT','MAINTENANCE','LEARNING','PORTFOLIO','FILE_MANIFEST','CHANGELOG'];
  for (const name of expected) if (!existsSync(resolve(root, `suite/docs/${name}.md`))) errors.push(`Missing document: ${name}`);
  for (const product of ['clientflow', 'supportdesk', 'invoicehub']) {
    for (const name of ['PRD','ARCHITECTURE','FILES','LEARNING']) if (!existsSync(resolve(root, `suite/docs/projects/${product}/${name}.md`))) errors.push(`Missing ${product}/${name}`);
    const ledger = resolve(root, `suite/docs/projects/${product}/FILES.md`);
    if (existsSync(ledger)) for (const row of readFileSync(ledger, 'utf8').split('\n')) {
      const cells = row.split('|').map(c => c.trim());
      if (cells.length >= 6 && cells[4].startsWith('verified')) {
        const path = cells[1].replaceAll('`', '');
        const full = resolve(root, path.startsWith('suite/') ? path : `suite/apps/${product}/${path}`);
        if (!existsSync(full)) errors.push(`Verified file absent: ${path}`);
      }
    }
  }
  const walk = dir => readdirSync(dir, { withFileTypes: true }).flatMap(e => e.isDirectory() ? walk(resolve(dir,e.name)) : e.name.endsWith('.md') ? [resolve(dir,e.name)] : []);
  const docs = [resolve(root,'AGENTS.md'),resolve(root,'README.md'),resolve(root,'suite/START_HERE.md'),...walk(resolve(root,'suite/docs'))];
  for (const doc of docs) {
    const content = readFileSync(doc,'utf8').replace(/```[\s\S]*?```/g, '');
    for (const [,target] of content.matchAll(/\[[^\]]+\]\(([^\s)]+)(?:\s+"[^"]*")?\)/g)) {
      if (/^(https?:|mailto:|#)/.test(target)) continue;
      const dest = resolve(dirname(doc), decodeURIComponent(target.split('#')[0]));
      if (!existsSync(dest)) errors.push(`${relative(root,doc)}: broken link ${target}`);
    }
  }
  return { errors, documents: docs.length };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
  const result = verifyRepository(root);
  if (result.errors.length) { console.error(result.errors.join('\n')); process.exitCode = 1; }
  else console.log(`Continuity checks passed: ${result.documents} documents; task dependencies, links, scope and verified file paths valid. This does not rerun feature tests.`);
}
