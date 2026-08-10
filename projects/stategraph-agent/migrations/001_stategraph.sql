create extension if not exists vector;
create table if not exists demo_users(id uuid primary key,name text not null,created_at timestamptz default now());
create table if not exists tasks(id uuid primary key,user_id uuid not null references demo_users(id),title text not null,input text not null,status text not null,created_at timestamptz default now());
create table if not exists task_runs(id uuid primary key,task_id uuid not null references tasks(id),thread_id uuid unique not null,current_node text not null,status text not null,error text,started_at timestamptz default now(),completed_at timestamptz);
create table if not exists agent_events(id uuid primary key,task_run_id uuid not null references task_runs(id),agent text not null,event_type text not null,input_summary text,output_summary text,duration_ms int,token_usage int default 0,created_at timestamptz default now());
create table if not exists approvals(id uuid primary key,task_run_id uuid not null references task_runs(id),reason text not null,risk_flags jsonb not null,status text not null,requested_at timestamptz default now(),resolved_at timestamptz,resolution_note text);
create table if not exists memories(id uuid primary key,user_id uuid not null references demo_users(id),memory_type text not null,content text not null,embedding vector(768),source_task_id uuid references tasks(id),created_at timestamptz default now());
create table if not exists graph_checkpoints(thread_id uuid primary key,state jsonb not null,version bigint not null default 1,updated_at timestamptz default now());
