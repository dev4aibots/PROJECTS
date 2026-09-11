import { statusLabels, type ProjectStatus } from '@/lib/projects';
export function StatusBadge({status}: {status: ProjectStatus}) { return <span className={`status-badge status-${status}`}><span className="status-dot" aria-hidden="true" />{statusLabels[status]}</span>; }
