'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ArrowUpRight, BookOpen, CirclesFour, FolderSimple, Flask, SquaresFour, X } from './icons';
import { useDemo } from './demo-provider';
import type { ReactNode } from 'react';
const nav = [{href:'/demo',label:'Overview',icon:SquaresFour}, {href:'/demo/projects',label:'Projects',icon:FolderSimple}, {href:'/demo/guide',label:'How it works',icon:BookOpen}];
export function AppShell({children}: {children: ReactNode}) {
  const path=usePathname(); const { projects, notice, dismissNotice }=useDemo();
  return <div className="app-layout">
    <aside className="sidebar">
      <Link href="/demo" className="brand" aria-label="ClientFlow overview"><span className="brand-mark"><CirclesFour size={25} weight="fill" aria-hidden="true" /></span>ClientFlow<span className="brand-period">.</span></Link>
      <div className="workspace"><span className="workspace-avatar">S<span aria-hidden="true">/</span></span><div><strong>Studio North</strong><span>Sample agency workspace</span></div></div>
      <p className="nav-caption">WORKSPACE</p>
      <nav aria-label="Main navigation">{nav.map(({href,label,icon:Icon}) => {const active=href==='/demo'?path===href:path.startsWith(href);return <Link key={href} href={href} aria-current={active?'page':undefined} className={`nav-link ${active?'current':''}`}><Icon size={20} weight={active?'fill':'regular'} aria-hidden="true"/>{label}{label==='Projects' && <span className="nav-count">{projects.length}</span>}</Link>;})}</nav>
      <div className="sidebar-bottom"><div className="sandbox-note"><Flask size={21} aria-hidden="true"/><strong>A workspace to explore.</strong><p>Create a project. Move it forward. Make yourself at home.</p><Link href="/demo/guide">About this demo <ArrowUpRight size={15} aria-hidden="true"/></Link></div><div className="workspace-footer"><span className="profile-mark" aria-hidden="true">SN</span><div><strong>Studio North</strong><span>Synthetic portfolio data</span></div></div></div>
    </aside>
    <div className="main-column">
      <header className="utility-header"><span>Workspace <span className="breadcrumb-slash">/</span> <strong>{path==='/demo'?'Overview':path.startsWith('/demo/projects')?'Projects':'Guide'}</strong></span><span className="demo-chip"><span aria-hidden="true"/> Interactive demo</span></header>
      <div className="demo-banner"><Flask size={16} aria-hidden="true"/><p><strong>Sample workspace.</strong> Changes stay in this tab while navigating. Reloading resets them.</p><Link href="/demo/guide">Details <ArrowUpRight size={14} aria-hidden="true"/></Link></div>
      <div className="notice" role="status" aria-live="polite">{notice && <><span>{notice}</span><button onClick={dismissNotice} aria-label="Dismiss notification"><X size={18} aria-hidden="true"/></button></>}</div>
      <main id="main-content" tabIndex={-1} className="main-content">{children}</main>
      <footer className="page-footer"><span>Made for work that moves forward.</span><span>Demo reference day · 7 Sep 2026</span></footer>
    </div>
  </div>;
}
