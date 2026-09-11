#!/usr/bin/env node
// gen-types.mjs — generate suite/apps/clientflow/src/lib/database.types.ts from
// the APPLIED local schema (CF-02), in the same shape `supabase gen types
// typescript` emits (Database.public.{Tables,Views,Functions,Enums,CompositeTypes}
// plus the Tables<>/Enums<> helper types), so supabase-js infers row types.
//
// Why not `supabase gen types --db-url`? The CLI requires Docker even for the
// db-url path (verified 2026-09-07: "docker: command not found"). This script
// introspects pg_catalog through psql, which is available wherever the
// migration chain itself can run. When Docker is available, the CLI output
// may be diffed against this file; both derive from the same catalog.
//
// Usage:
//   DATABASE_URL=postgres://... node suite/supabase/scripts/gen-types.mjs           # write
//   DATABASE_URL=postgres://... node suite/supabase/scripts/gen-types.mjs --check   # drift check (exit 1 on diff)
//   node suite/supabase/scripts/gen-types.mjs --self-test                             # mapping unit checks, no DB
//
// Deliberate differences from the CLI (documented in suite/docs/DATABASE.md):
//   * Objects owned by extensions (pgtap, pgcrypto) are excluded.
//   * Insert/Update only list columns the `authenticated` role may actually
//     INSERT/UPDATE (column-level grants). Server-managed columns such as
//     created_by/created_at are therefore absent from Insert/Update but present
//     in Row. The CLI ignores grants and would advertise writes that the
//     database rejects with 42501.
//
// Only reads catalogs. Never modifies the database. Refuses hosted hosts.

import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(here, '../../apps/clientflow/src/lib/database.types.ts');
const SCHEMA = 'public';
const args = new Set(process.argv.slice(2));

// ---------------------------------------------------------------------------
// Type mapping (mirrors postgres-meta's typescript generator)
// ---------------------------------------------------------------------------
export const PG_TO_TS = {
  bool: 'boolean',
  int2: 'number', int4: 'number', float4: 'number', float8: 'number', oid: 'number',
  int8: 'number', numeric: 'number', // supabase emits number for these too
  bytea: 'string', bpchar: 'string', varchar: 'string', text: 'string', citext: 'string',
  date: 'string', time: 'string', timetz: 'string', timestamp: 'string', timestamptz: 'string',
  uuid: 'string', money: 'string', inet: 'unknown', cidr: 'unknown',
  json: 'Json', jsonb: 'Json',
  void: 'undefined', record: 'Record<string, unknown>',
};

export function tsType(pgName, { enums, composites, tables }) {
  // Arrays come from pg_type.typname prefixed with '_' (e.g. _text, _platform_role)
  if (pgName.startsWith('_')) return `${tsType(pgName.slice(1), { enums, composites, tables })}[]`;
  if (PG_TO_TS[pgName]) return PG_TO_TS[pgName];
  if (enums.has(pgName)) return `Database["${SCHEMA}"]["Enums"]["${pgName}"]`;
  if (composites.has(pgName)) return `Database["${SCHEMA}"]["CompositeTypes"]["${pgName}"]`;
  if (tables.has(pgName)) return `Database["${SCHEMA}"]["Tables"]["${pgName}"]["Row"]`;
  return 'unknown';
}

// ---------------------------------------------------------------------------
// Catalog queries. Each returns CSV via psql; we parse with a tiny RFC4180 reader.
// ---------------------------------------------------------------------------
function parseCsv(text) {
  const rows = []; let row = []; let field = ''; let quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"') { if (text[i + 1] === '"') { field += '"'; i++; } else quoted = false; }
      else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ',') { row.push(field); field = ''; }
    else if (c === '\n') { row.push(field); rows.push(row); row = []; field = ''; }
    else if (c !== '\r') field += c;
  }
  if (field.length || row.length) { row.push(field); rows.push(row); }
  const [header, ...body] = rows;
  return body.filter(r => r.length === header.length).map(r => Object.fromEntries(header.map((h, i) => [h, r[i]])));
}

function refuseHosted(url) {
  if (/supabase\.(co|com)|pooler/i.test(url)) {
    console.error('gen-types: refusing to introspect a hosted database URL; run against a local reset DB.');
    process.exit(2);
  }
}

function query(sql) {
  const url = process.env.DATABASE_URL;
  if (!url) { console.error('gen-types: set DATABASE_URL (local throwaway database).'); process.exit(2); }
  refuseHosted(url);
  const out = execFileSync('psql', [url, '--csv', '-X', '-q', '-v', 'ON_ERROR_STOP=1', '-c', sql], { encoding: 'utf8' });
  return parseCsv(out);
}

const Q = {
  tables: `
    select c.relname as name, c.relkind as kind
    from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = '${SCHEMA}' and c.relkind in ('r','p','v','m')
      and not exists (select 1 from pg_depend d where d.classid = 'pg_class'::regclass and d.objid = c.oid and d.deptype = 'e')
    order by c.relname`,
  columnGrants: `
    select table_name, column_name, privilege_type
    from information_schema.column_privileges
    where table_schema = '${SCHEMA}' and grantee = 'authenticated' and privilege_type in ('INSERT','UPDATE')
    order by table_name, column_name, privilege_type`,
  columns: `
    select c.relname as table_name, a.attname as name, a.attnum as ordinal,
           t.typname as type_name, tn.nspname as type_schema,
           a.attnotnull as not_null,
           (a.atthasdef or a.attidentity <> '' or a.attgenerated <> '') as has_default,
           (a.attgenerated <> '') as is_generated
    from pg_attribute a
    join pg_class c on c.oid = a.attrelid
    join pg_namespace n on n.oid = c.relnamespace
    join pg_type t on t.oid = a.atttypid
    join pg_namespace tn on tn.oid = t.typnamespace
    where n.nspname = '${SCHEMA}' and c.relkind in ('r','p','v','m') and a.attnum > 0 and not a.attisdropped
    order by c.relname, a.attnum`,
  fks: `
    select con.conname as name, c.relname as table_name, fc.relname as referenced_table,
           (select string_agg(a.attname, ',' order by k.ord)
              from unnest(con.conkey) with ordinality k(attnum, ord)
              join pg_attribute a on a.attrelid = con.conrelid and a.attnum = k.attnum) as columns,
           (select string_agg(a.attname, ',' order by k.ord)
              from unnest(con.confkey) with ordinality k(attnum, ord)
              join pg_attribute a on a.attrelid = con.confrelid and a.attnum = k.attnum) as referenced_columns,
           exists (select 1 from pg_index i where i.indrelid = con.conrelid and i.indisunique
                     and i.indkey::int2[] operator(pg_catalog.@>) con.conkey and i.indkey::int2[] operator(pg_catalog.<@) con.conkey) as is_one_to_one
    from pg_constraint con
    join pg_class c on c.oid = con.conrelid
    join pg_class fc on fc.oid = con.confrelid
    join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = '${SCHEMA}' and con.contype = 'f'
    order by c.relname, con.conname`,
  enums: `
    select t.typname as name, string_agg(e.enumlabel, E'\\u0001' order by e.enumsortorder) as labels
    from pg_type t join pg_namespace n on n.oid = t.typnamespace
    join pg_enum e on e.enumtypid = t.oid
    where n.nspname = '${SCHEMA}' and t.typtype = 'e'
      and not exists (select 1 from pg_depend d where d.classid = 'pg_type'::regclass and d.objid = t.oid and d.deptype = 'e')
    group by t.typname order by t.typname`,
  composites: `
    select t.typname as name, a.attname as column_name, at.typname as type_name
    from pg_type t join pg_namespace n on n.oid = t.typnamespace
    join pg_class c on c.oid = t.typrelid and c.relkind = 'c'
    join pg_attribute a on a.attrelid = c.oid and a.attnum > 0 and not a.attisdropped
    join pg_type at on at.oid = a.atttypid
    where n.nspname = '${SCHEMA}' and t.typtype = 'c'
      and not exists (select 1 from pg_depend d where d.classid = 'pg_type'::regclass and d.objid = t.oid and d.deptype = 'e')
    order by t.typname, a.attnum`,
  functions: `
    select p.proname as name, p.oid as oid,
           pg_get_function_identity_arguments(p.oid) as identity_args,
           rt.typname as return_type, p.proretset as returns_set,
           coalesce(array_to_string(p.proargnames, E'\\u0001'), '') as arg_names,
           (select string_agg(t.typname, E'\\u0001' order by k.ord)
              from unnest(p.proargtypes::oid[]) with ordinality k(oid, ord)
              join pg_type t on t.oid = k.oid) as arg_types,
           coalesce(array_to_string(p.proargmodes, E'\\u0001'), '') as arg_modes,
           p.pronargdefaults as n_defaults, p.prokind as kind,
           exists (select 1 from information_schema.role_routine_grants g
                     where g.specific_schema = '${SCHEMA}' and g.specific_name = p.proname || '_' || p.oid
                       and g.grantee in ('anon','authenticated') and g.privilege_type = 'EXECUTE') as request_role_can_execute
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
    join pg_type rt on rt.oid = p.prorettype
    where n.nspname = '${SCHEMA}' and p.prokind in ('f','p')
      and not exists (select 1 from pg_depend d where d.classid = 'pg_proc'::regclass and d.objid = p.oid and d.deptype = 'e')
    order by p.proname, p.oid`,
};

// ---------------------------------------------------------------------------
// Emitters
// ---------------------------------------------------------------------------
const q = s => JSON.stringify(s);

export function buildModel(raw) {
  const enums = new Map(raw.enums.map(e => [e.name, e.labels.split('\u0001')]));
  const composites = new Map();
  for (const c of raw.composites) {
    if (!composites.has(c.name)) composites.set(c.name, []);
    composites.get(c.name).push({ name: c.column_name, type: c.type_name });
  }
  const tables = new Map();
  for (const t of raw.tables) tables.set(t.name, { kind: t.kind, columns: [], relationships: [] });
  for (const col of raw.columns) tables.get(col.table_name)?.columns.push(col);
  for (const fk of raw.fks) tables.get(fk.table_name)?.relationships.push(fk);
  // Column-level write privileges of the request role decide Insert/Update shape.
  const grants = new Map(); // table -> { INSERT:Set, UPDATE:Set }
  for (const g of raw.columnGrants ?? []) {
    if (!grants.has(g.table_name)) grants.set(g.table_name, { INSERT: new Set(), UPDATE: new Set() });
    grants.get(g.table_name)[g.privilege_type].add(g.column_name);
  }
  for (const [name, t] of tables) {
    const g = grants.get(name) ?? { INSERT: new Set(), UPDATE: new Set() };
    t.insertable = g.INSERT;
    t.updatable = g.UPDATE;
  }
  const functions = [];
  for (const f of raw.functions) {
    if (f.kind !== 'f') continue; // procedures are not callable via rpc
    if (f.return_type === 'trigger' || f.return_type === 'event_trigger') continue;
    const names = f.arg_names ? f.arg_names.split('\u0001') : [];
    const types = f.arg_types ? f.arg_types.split('\u0001') : [];
    const modes = f.arg_modes ? f.arg_modes.split('\u0001') : [];
    const inArgs = [];
    types.forEach((t, i) => {
      const mode = modes[i] ?? 'i';
      if (mode === 'i' || mode === 'b' || mode === 'v') inArgs.push({ name: names[i] || `arg${i + 1}`, type: t });
    });
    const nDefaults = Number(f.n_defaults);
    inArgs.forEach((a, i) => { a.hasDefault = i >= inArgs.length - nDefaults; });
    functions.push({
      name: f.name, args: inArgs, returnType: f.return_type, returnsSet: f.returns_set === 't',
      requestRoleCanExecute: f.request_role_can_execute === 't',
    });
  }
  return { enums, composites, tables, functions };
}

export function emit(model) {
  const ctx = { enums: model.enums, composites: model.composites, tables: model.tables };
  const lines = [];
  const p = (s = '') => lines.push(s);
  p('// GENERATED FILE — do not edit by hand (ADR-006).');
  p('// Source: applied migration chain in suite/supabase/migrations, introspected by');
  p('// suite/supabase/scripts/gen-types.mjs. Regenerate: npm run db:types');
  p('// Verify no drift: npm run db:types:check');
  p();
  p('export type Json =');
  p('  | string');
  p('  | number');
  p('  | boolean');
  p('  | null');
  p('  | { [key: string]: Json | undefined }');
  p('  | Json[]');
  p();
  p('export type Database = {');
  p(`  ${SCHEMA}: {`);

  // Tables / Views
  const emitRelations = (kinds, label) => {
    const rels = [...model.tables.entries()].filter(([, t]) => kinds.includes(t.kind));
    p(`    ${label}: {`);
    if (!rels.length) p('      [_ in never]: never');
    for (const [name, t] of rels) {
      p(`      ${name}: {`);
      p('        Row: {');
      for (const c of t.columns) p(`          ${c.name}: ${tsType(c.type_name, ctx)}${c.not_null === 't' ? '' : ' | null'}`);
      p('        }');
      if (label === 'Tables') {
        const ins = t.columns.filter(c => c.is_generated !== 't' && t.insertable.has(c.name));
        const upd = t.columns.filter(c => c.is_generated !== 't' && t.updatable.has(c.name));
        p(`        Insert: ${ins.length ? '{' : 'never // authenticated has no INSERT grant; use an rpc function'}`);
        for (const c of ins) {
          const optional = c.not_null !== 't' || c.has_default === 't';
          p(`          ${c.name}${optional ? '?' : ''}: ${tsType(c.type_name, ctx)}${c.not_null === 't' ? '' : ' | null'}`);
        }
        if (ins.length) p('        }');
        p(`        Update: ${upd.length ? '{' : 'never // authenticated has no UPDATE grant'}`);
        for (const c of upd) p(`          ${c.name}?: ${tsType(c.type_name, ctx)}${c.not_null === 't' ? '' : ' | null'}`);
        if (upd.length) p('        }');
      }
      p('        Relationships: [');
      for (const r of t.relationships) {
        p('          {');
        p(`            foreignKeyName: ${q(r.name)}`);
        p(`            columns: [${r.columns.split(',').map(q).join(', ')}]`);
        p(`            isOneToOne: ${r.is_one_to_one === 't'}`);
        p(`            referencedRelation: ${q(r.referenced_table)}`);
        p(`            referencedColumns: [${r.referenced_columns.split(',').map(q).join(', ')}]`);
        p('          },');
      }
      p('        ]');
      p('      }');
    }
    p('    }');
  };
  emitRelations(['r', 'p'], 'Tables');
  emitRelations(['v', 'm'], 'Views');

  // Functions — only those request roles can call (rpc surface). Internal
  // security-definer helpers without a grant are excluded on purpose so the
  // app cannot type-check a call the database will refuse.
  const fns = model.functions.filter(f => f.requestRoleCanExecute);
  p('    Functions: {');
  if (!fns.length) p('      [_ in never]: never');
  for (const f of fns) {
    p(`      ${f.name}: {`);
    if (!f.args.length) p('        Args: Record<PropertyKey, never>');
    else {
      p('        Args: {');
      for (const a of f.args) p(`          ${a.name}${a.hasDefault ? '?' : ''}: ${tsType(a.type, ctx)}`);
      p('        }');
    }
    const ret = tsType(f.returnType, ctx);
    p(`        Returns: ${f.returnsSet ? `${ret}[]` : ret}`);
    p('      }');
  }
  p('    }');

  // Enums
  p('    Enums: {');
  if (!model.enums.size) p('      [_ in never]: never');
  for (const [name, labels] of model.enums) p(`      ${name}: ${labels.map(q).join(' | ')}`);
  p('    }');

  // Composite types
  p('    CompositeTypes: {');
  if (!model.composites.size) p('      [_ in never]: never');
  for (const [name, cols] of model.composites) {
    p(`      ${name}: {`);
    for (const c of cols) p(`        ${c.name}: ${tsType(c.type, ctx)} | null`);
    p('      }');
  }
  p('    }');
  p('  }');
  p('}');
  p();
  // Helper types (same names supabase-js users expect)
  p(`type PublicSchema = Database[${q(SCHEMA)}]`);
  p();
  p('export type Tables<T extends keyof PublicSchema["Tables"]> = PublicSchema["Tables"][T]["Row"]');
  p('export type TablesInsert<T extends keyof PublicSchema["Tables"]> = PublicSchema["Tables"][T]["Insert"]');
  p('export type TablesUpdate<T extends keyof PublicSchema["Tables"]> = PublicSchema["Tables"][T]["Update"]');
  p('export type Enums<T extends keyof PublicSchema["Enums"]> = PublicSchema["Enums"][T]');
  p('export type Functions<T extends keyof PublicSchema["Functions"]> = PublicSchema["Functions"][T]');
  p();
  p('export const Constants = {');
  p(`  ${SCHEMA}: {`);
  p('    Enums: {');
  for (const [name, labels] of model.enums) p(`      ${name}: [${labels.map(q).join(', ')}],`);
  p('    },');
  p('  },');
  p('} as const');
  p();
  return lines.join('\n');
}

// ---------------------------------------------------------------------------
// Self-test: mapping and emitter on a fixed fixture (no database needed).
// ---------------------------------------------------------------------------
function selfTest() {
  const fixture = {
    tables: [{ name: 't', kind: 'r' }],
    columns: [
      { table_name: 't', name: 'id', ordinal: '1', type_name: 'uuid', type_schema: 'pg_catalog', not_null: 't', has_default: 't', is_generated: 'f' },
      { table_name: 't', name: 'kind', ordinal: '2', type_name: 'e', type_schema: 'public', not_null: 't', has_default: 'f', is_generated: 'f' },
      { table_name: 't', name: 'tags', ordinal: '3', type_name: '_text', type_schema: 'pg_catalog', not_null: 'f', has_default: 'f', is_generated: 'f' },
      { table_name: 't', name: 'total', ordinal: '4', type_name: 'int4', type_schema: 'pg_catalog', not_null: 't', has_default: 't', is_generated: 't' },
    ],
    fks: [{ name: 'fk', table_name: 't', referenced_table: 'u', columns: 'a,b', referenced_columns: 'c,d', is_one_to_one: 'f' }],
    columnGrants: [
      { table_name: 't', column_name: 'id', privilege_type: 'INSERT' },
      { table_name: 't', column_name: 'kind', privilege_type: 'INSERT' },
      { table_name: 't', column_name: 'tags', privilege_type: 'INSERT' },
      { table_name: 't', column_name: 'total', privilege_type: 'INSERT' },
      { table_name: 't', column_name: 'tags', privilege_type: 'UPDATE' },
    ],
    enums: [{ name: 'e', labels: 'x\u0001y' }],
    composites: [],
    functions: [
      { name: 'f', oid: '1', return_type: 'uuid', returns_set: 'f', arg_names: 'a\u0001b', arg_types: 'e\u0001text', arg_modes: '', n_defaults: '1', kind: 'f', request_role_can_execute: 't' },
      { name: 'hidden', oid: '2', return_type: 'bool', returns_set: 'f', arg_names: '', arg_types: '', arg_modes: '', n_defaults: '0', kind: 'f', request_role_can_execute: 'f' },
      { name: 'trg', oid: '3', return_type: 'trigger', returns_set: 'f', arg_names: '', arg_types: '', arg_modes: '', n_defaults: '0', kind: 'f', request_role_can_execute: 't' },
    ],
  };
  const out = emit(buildModel(fixture));
  const must = [
    'id: string', 'kind: Database["public"]["Enums"]["e"]', 'tags: string[] | null',
    'id?: string', 'kind: Database["public"]["Enums"]["e"]\n', // Insert keeps required enum
    'columns: ["a", "b"]', 'referencedColumns: ["c", "d"]',
    'e: "x" | "y"', 'a: Database["public"]["Enums"]["e"]', 'b?: string', 'Returns: string',
  ];
  const mustNot = ['hidden:', 'trg:', 'total?:', 'kind?:', 'Insert: never', 'Update: never'];
  const fails = [
    ...must.filter(s => !out.includes(s)).map(s => `missing ${JSON.stringify(s)}`),
    ...mustNot.filter(s => out.includes(s)).map(s => `unexpected ${JSON.stringify(s)}`),
  ];
  // Generated columns appear in Row but not Insert/Update
  if (!/Row: \{[^}]*total: number/s.test(out)) fails.push('generated column missing from Row');
  // Update lists only columns with an UPDATE grant (tags), never ungranted ones (id/kind)
  const upd = out.match(/Update: \{([^}]*)\}/s)?.[1] ?? '';
  if (!upd.includes('tags?:') || upd.includes('id?:') || upd.includes('kind?:')) fails.push('Update shape must follow UPDATE column grants');
  // A table with no write grants gets `never` for Insert/Update
  const ro = emit(buildModel({ ...fixture, columnGrants: [] }));
  if (!ro.includes('Insert: never') || !ro.includes('Update: never')) fails.push('ungranted table must emit never for Insert/Update');
  if (fails.length) { console.error('gen-types self-test FAILED:\n  ' + fails.join('\n  ')); process.exit(1); }
  console.log('gen-types self-test passed (mapping, arrays, enums, composite FK, defaults, rpc surface filter).');
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
if (args.has('--self-test')) {
  selfTest();
} else {
  const raw = {
    tables: query(Q.tables), columns: query(Q.columns), fks: query(Q.fks), columnGrants: query(Q.columnGrants),
    enums: query(Q.enums), composites: query(Q.composites), functions: query(Q.functions),
  };
  const model = buildModel(raw);
  const output = emit(model);
  const rpc = model.functions.filter(f => f.requestRoleCanExecute).length;
  if (args.has('--check')) {
    const current = existsSync(OUT) ? readFileSync(OUT, 'utf8') : '';
    if (current !== output) {
      console.error(`gen-types: DRIFT — ${OUT} does not match the applied schema. Run: npm run db:types`);
      process.exit(1);
    }
    console.log(`gen-types: no drift (${model.tables.size} tables, ${model.enums.size} enums, ${rpc} rpc functions).`);
  } else {
    writeFileSync(OUT, output);
    console.log(`Wrote ${OUT}: ${model.tables.size} tables, ${model.enums.size} enums, ${rpc} rpc functions.`);
  }
}
