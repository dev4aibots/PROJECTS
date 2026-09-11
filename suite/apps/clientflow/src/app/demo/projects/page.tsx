import { Suspense } from 'react';
import { ProjectWorkbench } from '@/components/project-workbench';
export const metadata={title:'Projects'};
export default function Page() {return <Suspense fallback={<p role="status">Loading project workbench…</p>}><ProjectWorkbench/></Suspense>;}
