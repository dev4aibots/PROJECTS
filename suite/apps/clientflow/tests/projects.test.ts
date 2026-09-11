import { describe, expect, it } from 'vitest';
import { addDays, dueSoon, filterProjects, formatDate, isCalendarDate, isOverdue, paginate, projectInputSchema, projectMetrics, saveProject } from '../src/lib/projects';
import { demoClients, demoProjects, DEMO_TODAY } from '../src/lib/demo-data';
const base = demoProjects[0];
const newId = '30000000-0000-4000-8000-000000000001';
describe('input and calendar validation', () => {
  it('trims name and description', () => expect(projectInputSchema.parse({...base,name:'  Project  ',description:' x '}).name).toBe('Project'));
  it.each(['', '   ', 'a'.repeat(101)])('rejects invalid name %j', name => expect(projectInputSchema.safeParse({...base,name}).success).toBe(false));
  it('rejects long description', () => expect(projectInputSchema.safeParse({...base,description:'a'.repeat(2001)}).success).toBe(false));
  it.each(['2026-02-29','2026-02-30','2026-13-01','2026-04-31','0000-01-01','not-date','2026-1-1'])('rejects invalid date %s', date => expect(isCalendarDate(date)).toBe(false));
  it.each(['2024-02-29','2026-12-31','0001-01-01'])('accepts real date %s', date => expect(isCalendarDate(date)).toBe(true));
  it('allows no deadline and past deadlines', () => {expect(projectInputSchema.safeParse({...base,dueDate:''}).success).toBe(true);expect(projectInputSchema.safeParse({...base,dueDate:'2020-01-01'}).success).toBe(true);});
  it('rejects unknown status and non-string values', () => {expect(projectInputSchema.safeParse({...base,status:'paid'}).success).toBe(false);expect(projectInputSchema.safeParse({...base,name:12}).success).toBe(false);});
});
describe('immutable mutations', () => {
  it('creates with UUID and trims input without mutating source', () => {const r=saveProject(demoProjects,demoClients,{...base,name:' New '},{id:newId});expect(r.ok).toBe(true);if(r.ok){expect(r.project.version).toBe(1);expect(r.project.name).toBe('New');expect(r.projects).toHaveLength(9);}expect(demoProjects).toHaveLength(8);});
  it('edits and increments version without mutating old row', () => {const r=saveProject(demoProjects,demoClients,{...base,status:'completed'},{id:base.id,expectedVersion:1});expect(r.ok).toBe(true);if(r.ok)expect(r.project.version).toBe(2);expect(base.status).toBe('active');});
  it('rejects stale version and duplicate creation ID', () => {for(const expectedVersion of [0,2,undefined,NaN])expect(saveProject(demoProjects,demoClients,base,{id:base.id,expectedVersion})).toMatchObject({ok:false,code:'conflict'});});
  it('rejects missing and malformed identity', () => {expect(saveProject(demoProjects,demoClients,base,{id:newId,expectedVersion:1})).toMatchObject({code:'not_found'});expect(saveProject(demoProjects,demoClients,base,{id:'bad'})).toMatchObject({code:'not_found'});});
  it('rejects nonexistent client', () => expect(saveProject(demoProjects,demoClients,{...base,clientId:newId},{id:newId})).toMatchObject({code:'validation',fields:{clientId:expect.any(String)}}));
  it('prevents assigning archived client but allows existing association', () => {const clients=demoClients.map(c=>({...c,archived:true}));expect(saveProject(demoProjects,clients,base,{id:newId})).toMatchObject({code:'validation'});expect(saveProject(demoProjects,clients,base,{id:base.id,expectedVersion:1}).ok).toBe(true);});
  it('returns field errors and does not apply partial edits', () => expect(saveProject(demoProjects,demoClients,{...base,name:''},{id:base.id,expectedVersion:1})).toMatchObject({ok:false,fields:{name:expect.any(String)}}));
  it('caps sample records without blocking edits', () => {const many=Array.from({length:200},(_,i)=>({...base,id:i===0?base.id:`p-${i}`}));expect(saveProject(many,demoClients,base,{id:newId})).toMatchObject({code:'limit'});expect(saveProject(many,demoClients,base,{id:base.id,expectedVersion:1}).ok).toBe(true);});
  it('strips unexpected privileged fields', () => {const r=saveProject([],demoClients,{...base,workspaceId:'foreign',version:100},{id:newId});if(!r.ok)throw new Error('Expected success');expect(r.project).not.toHaveProperty('workspaceId');expect(r.project.version).toBe(1);});
});
describe('derived views', () => {
  it('computes counts from same dataset', () => expect(projectMetrics(demoProjects,DEMO_TODAY)).toEqual({total:8,open:6,active:3,review:2,overdue:1,dueSoon:3,completed:1}));
  it('excludes completed/archived and no-deadline from overdue', () => {for(const p of [{...base,status:'completed' as const},{...base,status:'archived' as const},{...base,dueDate:''}])expect(isOverdue(p,'2030-01-01')).toBe(false);});
  it('due today is not overdue and seven-day boundary is inclusive', () => {expect(isOverdue({...base,dueDate:DEMO_TODAY},DEMO_TODAY)).toBe(false);expect(dueSoon({...base,dueDate:'2026-09-14'},DEMO_TODAY)).toBe(true);expect(dueSoon({...base,dueDate:'2026-09-15'},DEMO_TODAY)).toBe(false);});
  it('handles year boundary and UTC display', () => {expect(addDays('2026-12-31',1)).toBe('2027-01-01');expect(formatDate('2026-09-07')).toBe('7 Sept');expect(formatDate('')).toBe('No deadline');});
  it('combines case-insensitive client search with status', () => expect(filterProjects(demoProjects,demoClients,{q:' NORTHSTAR ',status:'active'},DEMO_TODAY).map(p=>p.name)).toEqual(['Customer portal']));
  it('attention filter and empty search results', () => {expect(filterProjects(demoProjects,demoClients,{attention:true},DEMO_TODAY)).toHaveLength(1);expect(filterProjects(demoProjects,demoClients,{q:'not found'},DEMO_TODAY)).toEqual([]);});
  it('handles empty metrics', () => expect(projectMetrics([],DEMO_TODAY).total).toBe(0));
  it('paginates and clamps invalid/out-of-range input', () => {const rows=Array.from({length:60},(_,i)=>i);expect(paginate(rows,2).items[0]).toBe(25);expect(paginate(rows,99).current).toBe(3);expect(paginate(rows,NaN).current).toBe(1);expect(paginate(rows,-2).current).toBe(1);expect(paginate([],2)).toMatchObject({items:[],current:1,pages:1});expect(()=>paginate(rows,1,0)).toThrow();});
});
