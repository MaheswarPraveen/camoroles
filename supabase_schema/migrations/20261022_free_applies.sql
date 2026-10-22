-- Free apply limits: 2 applies before signing in, 5 in total on a free account, unlimited on Pro.
-- One row per (person, job). Opening a job you already applied to again never costs anything.

create table if not exists public.job_applies (
  id bigserial primary key,
  user_id uuid references auth.users(id) on delete cascade,  -- null until the visitor signs in
  device_id text,                                             -- random id kept in the visitor's browser
  job_id uuid not null,
  created_at timestamptz not null default now()
);
create unique index if not exists job_applies_user_job on public.job_applies (user_id, job_id) where user_id is not null;
create unique index if not exists job_applies_device_job on public.job_applies (device_id, job_id) where user_id is null;
create index if not exists job_applies_device_idx on public.job_applies (device_id) where user_id is null;
alter table public.job_applies enable row level security;  -- server (service role) only

-- Checks the limit and records the apply in one step, so two quick taps can't both slip through.
-- p_job null = status only. Returns {allowed, need ('login'|'pay'|null), used}.
create or replace function public.job_apply_claim(
  p_user uuid, p_device text, p_job uuid,
  p_anon_limit int, p_user_limit int, p_unlimited boolean
) returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_used int;
  v_already boolean;
begin
  -- Applies made on this device before signing in move to the account.
  if p_user is not null and coalesce(p_device, '') <> '' then
    delete from job_applies d
     where d.user_id is null and d.device_id = p_device
       and exists (select 1 from job_applies u where u.user_id = p_user and u.job_id = d.job_id);
    update job_applies set user_id = p_user where user_id is null and device_id = p_device;
  end if;

  if p_user is not null then
    perform pg_advisory_xact_lock(hashtext(p_user::text));
    select count(*) into v_used from job_applies where user_id = p_user;
    select exists (select 1 from job_applies where user_id = p_user and job_id = p_job) into v_already;
  else
    if coalesce(p_device, '') = '' then
      return jsonb_build_object('allowed', false, 'need', 'login', 'used', 0);
    end if;
    perform pg_advisory_xact_lock(hashtext(p_device));
    select count(*) into v_used from job_applies where user_id is null and device_id = p_device;
    select exists (select 1 from job_applies where user_id is null and device_id = p_device and job_id = p_job) into v_already;
  end if;

  if p_job is null then
    return jsonb_build_object('allowed', true, 'need', null, 'used', v_used);
  end if;
  if v_already then
    return jsonb_build_object('allowed', true, 'need', null, 'used', v_used);
  end if;
  if not p_unlimited then
    if p_user is null and v_used >= p_anon_limit then
      return jsonb_build_object('allowed', false, 'need', 'login', 'used', v_used);
    end if;
    if p_user is not null and v_used >= p_user_limit then
      return jsonb_build_object('allowed', false, 'need', 'pay', 'used', v_used);
    end if;
  end if;

  insert into job_applies (user_id, device_id, job_id) values (p_user, nullif(p_device, ''), p_job)
  on conflict do nothing;
  return jsonb_build_object('allowed', true, 'need', null, 'used', v_used + 1);
end;
$$;

revoke all on function public.job_apply_claim(uuid, text, uuid, int, int, boolean) from public, anon, authenticated;
