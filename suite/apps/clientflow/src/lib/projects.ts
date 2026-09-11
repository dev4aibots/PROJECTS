import { z } from 'zod';

export const projectStatuses = ['planned', 'active', 'review', 'completed', 'archived'] as const;
export type ProjectStatus = (typeof projectStatuses)[number];
export const statusLabels: Record<ProjectStatus, string> = { planned: 'Planned', active: 'In progress', review: 'In review', completed: 'Completed', archived: 'Archived' };
export type Client = { id: string; name: string; initials: string; color: string; archived?: boolean };
export function isCalendarDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || value < '0001-01-01') return false;
  const parsed = new Date(`${value}T00:00:00.000Z`);
  return !Number.isNaN(parsed.valueOf()) && parsed.toISOString().slice(0, 10) === value;
}
export const projectInputSchema = z.object({
  name: z.string().trim().min(1, 'Enter a project name.').max(100, 'Use 100 characters or fewer.'),
  description: z.string().trim().max(2000, 'Use 2,000 characters or fewer.'),
  clientId: z.uuid('Choose a valid client.'),
  status: z.enum(projectStatuses, { error: 'Choose a valid project status.' }),
  dueDate: z.string().refine(v => v === '' || isCalendarDate(v), 'Enter a real date (YYYY-MM-DD).'),
});
export type ProjectInput = z.infer<typeof projectInputSchema>;
export type Project = ProjectInput & { id: string; version: number };
export type FieldErrors = Partial<Record<keyof ProjectInput, string>>;
export type SaveResult = { ok: true; project: Project; projects: Project[] } | { ok: false; code: 'validation' | 'not_found' | 'conflict' | 'limit'; message: string; fields?: FieldErrors };

/** Pure mutation contract. The future server/DB must independently enforce it. */
export function saveProject(projects: Project[], clients: Client[], input: unknown, command: { id: string; expectedVersion?: number }): SaveResult {
  const parsed = projectInputSchema.safeParse(input);
  if (!parsed.success) {
    const fields: FieldErrors = {};
    for (const issue of parsed.error.issues) { const key = issue.path[0] as keyof ProjectInput; if (!fields[key]) fields[key] = issue.message; }
    return { ok: false, code: 'validation', message: 'Check the highlighted fields.', fields };
  }
  if (!z.uuid().safeParse(command.id).success) return { ok: false, code: 'not_found', message: 'This project could not be found. Return to projects.' };
  const existing = projects.find(p => p.id === command.id);
  if (command.expectedVersion !== undefined && !existing) return { ok: false, code: 'not_found', message: 'This project no longer exists. Return to projects.' };
  if (existing && (existing.version !== command.expectedVersion || !Number.isSafeInteger(command.expectedVersion))) return { ok: false, code: 'conflict', message: 'This project changed after you opened it. Reload the latest version, then reapply your changes.' };
  const client = clients.find(c => c.id === parsed.data.clientId);
  if (!client || (client.archived && existing?.clientId !== client.id)) return { ok: false, code: 'validation', message: 'Choose an available client.', fields: {clientId: 'Choose an available client.'} };
  if (!existing && projects.length >= 200) return { ok: false, code: 'limit', message: 'This sample workspace has reached 200 projects. Reset the demo to start again.' };
  const project: Project = { ...parsed.data, id: command.id, version: (existing?.version ?? 0) + 1 };
  return { ok: true, project, projects: existing ? projects.map(p => p.id === project.id ? project : p) : [project, ...projects] };
}

export function isOpen(project: Project) { return project.status !== 'completed' && project.status !== 'archived'; }
export function isOverdue(project: Project, today: string) { return isOpen(project) && !!project.dueDate && project.dueDate < today; }
export function addDays(date: string, amount: number) { const d = new Date(`${date}T00:00:00Z`); d.setUTCDate(d.getUTCDate() + amount); return d.toISOString().slice(0,10); }
export function dueSoon(project: Project, today: string) { return isOpen(project) && !!project.dueDate && project.dueDate >= today && project.dueDate <= addDays(today,7); }
export function filterProjects(projects: Project[], clients: Client[], query: { q?: string; status?: string; attention?: boolean }, today: string) {
  const needle = (query.q ?? '').trim().toLocaleLowerCase('en');
  const names = new Map(clients.map(c => [c.id, c.name]));
  return projects.filter(p => (!query.status || query.status === 'all' || p.status === query.status) && (!query.attention || isOverdue(p,today)) && `${p.name} ${names.get(p.clientId) ?? ''}`.toLocaleLowerCase('en').includes(needle));
}
export function projectMetrics(projects: Project[], today: string) {
  return { total: projects.length, open: projects.filter(isOpen).length, active: projects.filter(p => p.status === 'active').length, review: projects.filter(p => p.status === 'review').length, overdue: projects.filter(p => isOverdue(p,today)).length, dueSoon: projects.filter(p => dueSoon(p,today)).length, completed: projects.filter(p => p.status === 'completed').length };
}
export function paginate<T>(items: T[], page: number, size = 25) {
  if (!Number.isSafeInteger(size) || size < 1) throw new Error('Page size must be a positive integer');
  const pages = Math.max(1, Math.ceil(items.length / size));
  const current = Math.max(1, Math.min(pages, Number.isSafeInteger(page) ? page : 1));
  return { items: items.slice((current-1)*size,current*size), current, pages, total: items.length };
}
export function formatDate(date: string) { return date ? new Intl.DateTimeFormat('en-GB', {day:'numeric',month:'short',timeZone:'UTC'}).format(new Date(`${date}T00:00:00Z`)) : 'No deadline'; }
