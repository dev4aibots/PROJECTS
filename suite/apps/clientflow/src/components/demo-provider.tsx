'use client';
import { createContext, useContext, useRef, useState, type ReactNode } from 'react';
import { demoClients, demoProjects, DEMO_TODAY } from '@/lib/demo-data';
import { saveProject, type Project, type SaveResult } from '@/lib/projects';
type DemoContextValue = { projects: Project[]; clients: typeof demoClients; today: string; notice: string; dismissNotice: () => void; save: (input: unknown, id?: string, expectedVersion?: number) => SaveResult; reset: () => void };
const DemoContext = createContext<DemoContextValue | null>(null);
export function DemoProvider({ children }: { children: ReactNode }) {
  const [projects, setProjects] = useState(() => demoProjects.map(p => ({...p})));
  const latest = useRef(projects);
  const [notice, setNotice] = useState('');
  function save(input: unknown, id?: string, expectedVersion?: number): SaveResult {
    const result = saveProject(latest.current, demoClients, input, {id: id ?? crypto.randomUUID(), expectedVersion});
    if (result.ok) { latest.current = result.projects; setProjects(result.projects); setNotice(`${result.project.name} ${id ? 'updated' : 'created'} in this demo session.`); }
    return result;
  }
  function reset() { const rows=demoProjects.map(p=>({...p})); latest.current=rows; setProjects(rows); setNotice('Demo reset to the original sample projects.'); }
  return <DemoContext.Provider value={{ projects, clients: demoClients, today: DEMO_TODAY, notice, dismissNotice: () => setNotice(''), save, reset }}>{children}</DemoContext.Provider>;
}
export function useDemo() { const context=useContext(DemoContext); if(!context) throw new Error('Demo context must be inside the explicit demo boundary'); return context; }
