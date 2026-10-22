-- Greenhouse board lists carry no description; jobs.description is NOT NULL, so every new Greenhouse
-- job made the harvest crash. Insert an empty description; the enrich step fills it in later.

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
         i.apply_url, coalesce(i.description, ''), i.experience_min, i.experience_max, coalesce(i.skills, '{}'), true, now()
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
