'use client';
import Link from 'next/link';
import { useDemo } from './demo-provider';
import { ProjectForm } from './project-form';
export function ProjectDetail({id}: {id:string}) { const {projects}=useDemo();const project=projects.find(p=>p.id===id);return project?<ProjectForm key={`${project.id}:${project.version}`} project={project}/>:<div className="empty-state"><h1>Project not found</h1><p>It may have been a temporary demo project cleared by a reload.</p><Link className="button primary" href="/demo/projects">Back to projects</Link></div>; }
