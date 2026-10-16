-- ==============================================================================
-- camOroles (Jobinator) — Complete Supabase Setup & Automated 5 AM Cron Triggers
-- Run this in the Supabase Dashboard: SQL Editor -> New Query -> Run
-- ==============================================================================

-- 1. Enable Core Extensions
create extension if not exists vector;
create extension if not exists pg_cron with schema extensions;
create extension if not exists pg_net with schema extensions;

-- 2. Jobs Inventory Table
create table if not exists public.jobs (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  company text not null,
  ats_type text not null check (ats_type in ('keka', 'darwinbox', 'zoho', 'lever', 'greenhouse', 'ashby', 'workable', 'recruitee', 'smartrecruiters', 'direct')),
  location text not null default 'Remote / Worldwide',
  is_remote boolean not null default false,
  experience_min int not null default 0,
  experience_max int not null default 3,
  apply_url text not null unique,
  description text not null,
  skills text[] not null default '{}',
  embedding vector(384),
  is_active boolean not null default true,
  last_verified_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index if not exists jobs_active_idx on public.jobs(is_active) where is_active is true;
create index if not exists jobs_ats_idx on public.jobs(ats_type);
create index if not exists jobs_created_idx on public.jobs(created_at desc);

-- 3. Candidate Profiles (Summaries & Embeddings only - raw PDFs are NEVER stored)
create table if not exists public.cv_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade unique,
  headline text,
  experience_years numeric not null default 0,
  skills text[] not null default '{}',
  summary text not null,
  embedding vector(384),
  updated_at timestamptz not null default now()
);

create index if not exists cv_profiles_user_idx on public.cv_profiles(user_id);

-- 4. Cached Job Matches (Evaluated once, cached permanently)
create table if not exists public.job_matches (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  job_id uuid not null references public.jobs(id) on delete cascade,
  similarity_score numeric not null,
  match_score int not null check (match_score between 1 and 100),
  why_matched text not null,
  status text not null default 'new' check (status in ('new', 'unlocked', 'applied', 'bad_match')),
  created_at timestamptz not null default now(),
  constraint job_matches_user_job_unique unique (user_id, job_id)
);

create index if not exists job_matches_user_score_idx on public.job_matches(user_id, match_score desc);
create index if not exists job_matches_job_idx on public.job_matches(job_id);

-- 5. User Entitlements (3 free unlocks/week & paid passes)
create table if not exists public.user_entitlements (
  user_id uuid primary key references auth.users(id) on delete cascade,
  unlimited_until timestamptz,
  free_unlocks_left int not null default 3,
  last_free_reset timestamptz not null default now(),
  created_at timestamptz not null default now()
);

-- 6. Razorpay Orders (One-time passes: ₹30/week, ₹100/month)
create table if not exists public.job_orders (
  id text primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  amount int not null,
  plan text not null check (plan in ('week', 'month')),
  status text not null default 'created' check (status in ('created', 'paid')),
  payment_id text,
  created_at timestamptz not null default now()
);

create index if not exists job_orders_user_idx on public.job_orders(user_id);

-- 7. Vector Similarity Matching RPC
create or replace function public.find_top_job_candidates(
  p_user_id uuid,
  p_limit int default 20,
  p_match_threshold float default 0.35
)
returns table (
  job_id uuid,
  title text,
  company text,
  location text,
  is_remote boolean,
  experience_min int,
  experience_max int,
  skills text[],
  description text,
  similarity float
)
language sql stable as $$
  with user_cv as (
    select embedding from public.cv_profiles where user_id = p_user_id limit 1
  )
  select
    j.id as job_id,
    j.title,
    j.company,
    j.location,
    j.is_remote,
    j.experience_min,
    j.experience_max,
    j.skills,
    j.description,
    1 - (j.embedding <=> u.embedding) as similarity
  from public.jobs j, user_cv u
  where j.is_active is true
    and j.embedding is not null
    and u.embedding is not null
    and not exists (
      select 1 from public.job_matches m
      where m.user_id = p_user_id and m.job_id = j.id
    )
    and (1 - (j.embedding <=> u.embedding)) >= p_match_threshold
  order by j.embedding <=> u.embedding
  limit p_limit;
$$;

-- 8. Row Level Security
alter table public.jobs enable row level security;
alter table public.cv_profiles enable row level security;
alter table public.job_matches enable row level security;
alter table public.user_entitlements enable row level security;
alter table public.job_orders enable row level security;

create policy "Public read active jobs" on public.jobs for select using (is_active is true);
create policy "Users own CV profile" on public.cv_profiles for all using (auth.uid() = user_id);
create policy "Users view their matches" on public.job_matches for all using (auth.uid() = user_id);
create policy "Users view entitlements" on public.user_entitlements for select using (auth.uid() = user_id);
create policy "Users view orders" on public.job_orders for select using (auth.uid() = user_id);

-- ==============================================================================
-- 9. In-Database Automated 5:00 AM IST Cron Schedules
-- ==============================================================================

-- Deactivate stale postings older than 14 days without re-verification (runs at 5:00 AM IST daily)
select cron.schedule(
  'daily-prune-stale-jobs-5am',
  '30 23 * * *',
  $$
    update public.jobs
    set is_active = false
    where is_active is true
      and last_verified_at < now() - interval '14 days';
  $$
);

-- Reset free weekly apply quota to 3 every Monday at 5:00 AM IST
select cron.schedule(
  'weekly-reset-free-unlocks-5am',
  '30 23 * * 0',
  $$
    update public.user_entitlements
    set free_unlocks_left = 3,
        last_free_reset = now()
    where free_unlocks_left < 3;
  $$
);
