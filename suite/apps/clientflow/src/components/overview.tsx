'use client';
import Link from 'next/link';
import { ArrowRight, Plus, WarningCircle } from './icons';
import { useDemo } from './demo-provider';
import { DeadlineRail, MetricStrip } from './project-workbench';
import { StatusBadge } from './status-badge';
import { isOpen, isOverdue } from '@/lib/projects';
export function Overview() {
  const {projects,clients,today}=useDemo(); const open=projects.filter(isOpen); const overdue=projects.filter(p=>isOverdue(p,today));
  return <><div className="page-heading"><div><span className="eyebrow">STUDIO NORTH / WORKSPACE OVERVIEW</span><h1>Good work starts here.</h1><p>Your projects, your next steps, a little more headspace.</p></div><Link className="button primary" href="/demo/projects/new"><Plus size={18} aria-hidden="true"/>New project</Link></div><MetricStrip/><div className="workbench-grid"><div><section className="overview-callout"><span className="eyebrow">YOUR WORKSPACE AT A GLANCE</span><h2>{open.length} projects.<br/>One clear direction.</h2><p>Keep the day-to-day connected to the bigger picture.<br/>Your next step is right where you left it.</p><Link className="button primary" href="/demo/projects">Open project workbench<ArrowRight size={18} aria-hidden="true"/></Link><div className="callout-art" aria-hidden="true"><div/><div/><div/></div></section>{overdue.length>0&&<Link className="attention-callout" href="/demo/projects?attention=1"><WarningCircle size={21} aria-hidden="true"/><div><strong>{overdue.length} project needs a deadline check</strong><span>Review the timeline and agree on the next step.</span></div><ArrowRight size={18} aria-hidden="true"/></Link>}<section className="overview-projects"><div className="section-heading"><h2>Work in motion</h2><Link href="/demo/projects">View all<ArrowRight size={15} aria-hidden="true"/></Link></div>{open.slice(0,4).map(p=><Link className="overview-row" href={`/demo/projects/${p.id}`} key={p.id}><div><strong>{p.name}</strong><span>{clients.find(c=>c.id===p.clientId)?.name}</span></div><StatusBadge status={p.status}/></Link>)}{!open.length&&<p>No open projects. Create one when you’re ready.</p>}</section></div><DeadlineRail/></div></>;
}
