import type { Client, Project, ProjectStatus } from './projects';
// Fixed business day keeps screenshots and overdue tests stable across timezones.
export const DEMO_TODAY = '2026-09-07';
export const demoClients: Client[] = [
  {id:'10000000-0000-4000-8000-000000000001',name:'Orbit Studio',initials:'OS',color:'violet'},
  {id:'10000000-0000-4000-8000-000000000002',name:'Forma Living',initials:'FL',color:'sand'},
  {id:'10000000-0000-4000-8000-000000000003',name:'Northstar Labs',initials:'NL',color:'blue'},
  {id:'10000000-0000-4000-8000-000000000004',name:'Fieldwork Coffee',initials:'FC',color:'rose'},
];
const rows: [string, number, ProjectStatus, string, string][] = [
  ['Brand & website refresh',0,'active','2026-09-18','Bring the Orbit identity to life with an editorial website, a clearer service story, and a flexible visual system.'],
  ['Autumn collection launch',1,'review','2026-09-09','Review the seasonal landing pages and product storytelling before the collection goes live.'],
  ['Customer portal',2,'active','2026-09-05','Design a calmer space for customers to manage their account and find product documentation.'],
  ['E-commerce experience',3,'active','2026-09-14','Rework the coffee discovery and subscription experience for a growing independent roaster.'],
  ['Design system foundations',2,'planned','2026-09-28','Create shared typography, component states, and accessible interaction patterns.'],
  ['Product photography site',1,'review','2026-09-11','A focused portfolio for the studio’s product photography and material studies.'],
  ['Spring campaign',0,'completed','2026-08-28','Campaign landing pages delivered for the spring collection.'],
  ['Menu & locations',3,'archived','2026-07-20','Previous iteration retained for reference.'],
];
export const demoProjects: Project[] = rows.map(([name, client, status, dueDate, description],i) => ({ id:`20000000-0000-4000-8000-${String(i+1).padStart(12,'0')}`, name, clientId:demoClients[client].id, status, dueDate, description, version:1 }));
