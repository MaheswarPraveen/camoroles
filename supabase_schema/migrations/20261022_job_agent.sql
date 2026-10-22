-- Job agent: keeps the jobs table in sync with company job boards.
-- Adds new postings, removes postings that left the board, checks other links,
-- and fills experience/skills from the real job description with an LLM.

alter table public.jobs add column if not exists source_key text;   -- e.g. greenhouse:anduril:5230154007
alter table public.jobs add column if not exists enriched_at timestamptz;
alter table public.jobs add column if not exists last_checked_at timestamptz;   -- last link check, even when the result was unclear
create index if not exists jobs_source_key_idx on public.jobs (source_key);
create index if not exists jobs_check_queue_idx on public.jobs (last_checked_at nulls first) where is_active is true and source_key is null;
create index if not exists jobs_enrich_queue_idx on public.jobs (created_at desc) where is_active is true and enriched_at is null;

-- Backfill keys from apply URLs we can parse.
update public.jobs set source_key = 'greenhouse:' || lower(m[1]) || ':' || m[2]
from (select id, regexp_match(apply_url, 'greenhouse\.io/([^/?#]+)/jobs/(\d+)') m from public.jobs) s
where jobs.id = s.id and s.m is not null and jobs.source_key is null;

update public.jobs set source_key = 'lever:' || lower(m[1]) || ':' || lower(m[2])
from (select id, regexp_match(apply_url, 'jobs\.(?:eu\.)?lever\.co/([^/?#]+)/([0-9a-fA-F-]{36})') m from public.jobs) s
where jobs.id = s.id and s.m is not null and jobs.source_key is null;

update public.jobs set source_key = 'ashby:' || lower(m[1]) || ':' || lower(m[2])
from (select id, regexp_match(apply_url, 'jobs\.ashbyhq\.com/([^/?#]+)/([0-9a-fA-F-]{36})') m from public.jobs) s
where jobs.id = s.id and s.m is not null and jobs.source_key is null;

-- Same posting stored under two URL spellings: keep the oldest row, retire the copies.
update public.jobs j set is_active = false, source_key = null
from (
  select id, row_number() over (partition by source_key order by is_active desc, created_at, id) rn
  from public.jobs where source_key is not null
) d
where j.id = d.id and d.rn > 1;

create table if not exists public.job_sources (
  id bigserial primary key,
  ats text not null check (ats in ('greenhouse', 'lever', 'ashby')),
  token text not null,
  company text not null,
  enabled boolean not null default true,
  last_run_at timestamptz,
  last_status text,
  jobs_seen int,
  created_at timestamptz not null default now(),
  unique (ats, token)
);

-- Every board that already has jobs in the table becomes a live source.
insert into public.job_sources (ats, token, company)
select split_part(source_key, ':', 1), split_part(source_key, ':', 2), mode() within group (order by company)
from public.jobs
where source_key is not null
group by 1, 2
on conflict (ats, token) do nothing;

create table if not exists public.job_agent_runs (
  id bigserial primary key,
  mode text not null,
  source text,
  added int not null default 0,
  removed int not null default 0,
  refreshed int not null default 0,
  enriched int not null default 0,
  note text,
  created_at timestamptz not null default now()
);
create index if not exists job_agent_runs_created_idx on public.job_agent_runs (created_at desc);

alter table public.job_sources enable row level security;
alter table public.job_agent_runs enable row level security;

-- Applies one full board listing: refresh what is still there, insert what is new,
-- deactivate what disappeared (only when the caller trusts the listing).
create or replace function public.job_agent_apply(p_prefix text, p_jobs jsonb, p_allow_remove boolean)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_refreshed int := 0;
  v_added int := 0;
  v_removed int := 0;
begin
  create temp table _in on commit drop as
  select * from jsonb_to_recordset(p_jobs) as x(
    source_key text, title text, company text, ats_type text, location text, is_remote boolean,
    apply_url text, description text, experience_min int, experience_max int, skills text[]
  );

  update jobs j
  set is_active = true,
      last_verified_at = now(),
      title = i.title,
      location = coalesce(nullif(i.location, ''), j.location),
      is_remote = j.is_remote or i.is_remote,
      description = case when j.enriched_at is null then coalesce(i.description, j.description) else j.description end
  from _in i
  where j.source_key = i.source_key;
  get diagnostics v_refreshed = row_count;

  insert into jobs (source_key, title, company, ats_type, location, is_remote, apply_url, description,
                    experience_min, experience_max, skills, is_active, last_verified_at)
  select i.source_key, i.title, i.company, i.ats_type, coalesce(nullif(i.location, ''), 'Remote / Worldwide'), i.is_remote,
         i.apply_url, i.description, i.experience_min, i.experience_max, coalesce(i.skills, '{}'), true, now()
  from _in i
  where not exists (select 1 from jobs j where j.source_key = i.source_key)
  on conflict (apply_url) do update
    set source_key = excluded.source_key, is_active = true, last_verified_at = now();
  get diagnostics v_added = row_count;

  if p_allow_remove then
    update jobs j
    set is_active = false, last_verified_at = now()
    where j.is_active
      and j.source_key like p_prefix || '%'
      and not exists (select 1 from _in i where i.source_key = j.source_key);
    get diagnostics v_removed = row_count;
  end if;

  return jsonb_build_object('refreshed', v_refreshed, 'added', v_added, 'removed', v_removed);
end;
$$;

revoke all on function public.job_agent_apply(text, jsonb, boolean) from public, anon, authenticated;
