'use client';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Check, FolderSimple, Info } from '@phosphor-icons/react';
import { useDemo } from './demo-provider';
import { projectStatuses, statusLabels, type FieldErrors, type Project, type ProjectInput } from '@/lib/projects';
export function ProjectForm({ project }: { project?: Project }) {
  const { clients, save }=useDemo(); const router=useRouter(); const busy=useRef(false); const saved=useRef(false);
  const initial: ProjectInput=project??{name:'',description:'',clientId:'',status:'planned',dueDate:''};
  const [values,setValues]=useState(initial); const [fields,setFields]=useState<FieldErrors>({}); const [error,setError]=useState(''); const [saving,setSaving]=useState(false);
  const dirty=JSON.stringify(values)!==JSON.stringify(initial);
  useEffect(()=>{
    if(!dirty)return;
    const before=(e: BeforeUnloadEvent)=>{if(!saved.current){e.preventDefault();e.returnValue='';}};
    const leave=(e: MouseEvent)=>{const link=(e.target as Element).closest('a[href]'); if(!saved.current&&link&&!link.getAttribute('href')?.startsWith('#')&&!window.confirm('Discard your unsaved project changes?')) {e.preventDefault();e.stopPropagation();}};
    window.addEventListener('beforeunload',before);document.addEventListener('click',leave,true);
    return()=>{window.removeEventListener('beforeunload',before);document.removeEventListener('click',leave,true);};
  },[dirty]);
  function change<K extends keyof ProjectInput>(key: K, value: ProjectInput[K]) {setValues(v=>({...v,[key]:value}));setFields(v=>({...v,[key]:undefined}));}
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); if(busy.current)return; busy.current=true; setSaving(true); setError('');
    const result=save(values,project?.id,project?.version);
    if(!result.ok){setFields(result.fields??{});setError(result.message);setSaving(false);busy.current=false;const first=Object.keys(result.fields??{})[0];requestAnimationFrame(()=>document.getElementById(first?`field-${first}`:'form-error')?.focus());return;}
    saved.current=true;router.push('/demo/projects');
  }
  const attrs=(key: keyof ProjectInput)=>({id:`field-${key}`,name:key,'aria-invalid':!!fields[key],'aria-describedby':fields[key]?`error-${key}`:undefined});
  const fieldError=(key: keyof ProjectInput)=>fields[key]?<p className="field-error" id={`error-${key}`}>{fields[key]}</p>:null;
  return <div className="form-page"><Link className="back-link" href="/demo/projects"><ArrowLeft size={17} aria-hidden="true"/>Back to projects</Link><div className="page-heading"><div><span className="eyebrow">A CLEAR START MAKES ALL THE DIFFERENCE</span><h1>{project?'Edit project':'New project'}</h1><p>{project?'Keep the details in step with the work.':'Bring the client, the goal, and the next deadline together.'}</p></div></div><div className="form-grid"><form className="project-form" onSubmit={submit} noValidate><div className="form-section-title"><FolderSimple size={20} aria-hidden="true"/><h2>Project details</h2></div>
    {error&&<div id="form-error" role="alert" className="form-error" tabIndex={-1}>{error}{!Object.keys(fields).length&&project&&<button type="button" onClick={()=>{saved.current=true;router.refresh();window.location.reload();}}>Reload sample workspace</button>}</div>}
    <div className="field"><label htmlFor="field-name">Project name <span className="required">(required)</span></label><input {...attrs('name')} value={values.name} onChange={e=>change('name',e.target.value)} maxLength={100} placeholder="e.g. Brand & website refresh…" autoComplete="off" required/>{fieldError('name')}</div>
    <div className="field"><label htmlFor="field-clientId">Client <span className="required">(required)</span></label><select {...attrs('clientId')} value={values.clientId} onChange={e=>change('clientId',e.target.value)} required><option value="">Choose a client</option>{clients.filter(c=>!c.archived||c.id===project?.clientId).map(c=><option value={c.id} key={c.id}>{c.name}</option>)}</select>{fieldError('clientId')}</div>
    <div className="two-fields"><div className="field"><label htmlFor="field-status">Status</label><select {...attrs('status')} value={values.status} onChange={e=>change('status',e.target.value as ProjectInput['status'])}>{projectStatuses.map(s=><option key={s} value={s}>{statusLabels[s]}</option>)}</select>{fieldError('status')}</div><div className="field"><label htmlFor="field-dueDate">Due date <span className="required">(optional)</span></label><input {...attrs('dueDate')} type="date" value={values.dueDate} onChange={e=>change('dueDate',e.target.value)} min="0001-01-01" max="9999-12-31"/>{fieldError('dueDate')}</div></div>
    <div className="field"><label htmlFor="field-description">Project brief <span className="required">(optional)</span></label><textarea {...attrs('description')} rows={5} value={values.description} onChange={e=>change('description',e.target.value)} maxLength={2000} placeholder="What are we making, and what does a good outcome look like?…"/><div className="field-hint"><span>A little context goes a long way.</span><span>{values.description.length}/2,000</span></div>{fieldError('description')}</div>
    <div className="form-actions"><Link className="button secondary" href="/demo/projects">Cancel</Link><button className="button primary" type="submit" disabled={saving}><Check size={18} aria-hidden="true"/>{saving?'Saving…':project?'Save changes':'Create project'}</button></div></form><aside className="form-aside"><Info size={23} aria-hidden="true"/><h2>Start with the essentials.</h2><p>A name and a client are all you need. You can come back to the brief and deadline as the project takes shape.</p><hr/><strong>This is a sample workspace</strong><p>Changes are kept in memory while you navigate. A page reload restores the sample data. Do not enter private client information.</p>{project&&<p className="version-note">Editing version {project.version}. Stale updates are rejected rather than silently overwriting newer work.</p>}</aside></div></div>;
}
