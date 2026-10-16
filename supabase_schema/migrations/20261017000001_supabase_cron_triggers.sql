-- Enable pg_cron and pg_net extensions for automated in-database scheduling and HTTP triggers
create extension if not exists pg_cron with schema extensions;
create extension if not exists pg_net with schema extensions;

-- 1. Scheduled Job: Daily Pruning of Stale Jobs at 5:00 AM IST (23:30 UTC)
-- Deactivates postings that have not been re-verified within the last 14 days
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

-- 2. Scheduled Job: Reset Free Weekly Apply Unlocks Every Monday at 5:00 AM IST (23:30 UTC Sunday)
-- Ensures every free user gets their fresh 3 apply links every week
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

-- 3. Stored Procedure: Trigger Cloud Crawler Webhook (GitHub Actions / Cloudflare / Server)
-- This allows Supabase to directly command external cloud scrapers to wake up at 5:00 AM IST
create or replace function public.dispatch_crawler_run(
  p_webhook_url text,
  p_auth_header text default null
)
returns bigint
language plpgsql
security definer
as $$
declare
  req_id bigint;
  headers_json jsonb;
begin
  if p_auth_header is not null then
    headers_json := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', p_auth_header
    );
  else
    headers_json := jsonb_build_object('Content-Type', 'application/json');
  end if;

  select net.http_post(
    url := p_webhook_url,
    headers := headers_json,
    body := jsonb_build_object('event', 'crawl_5am', 'timestamp', now())
  ) into req_id;

  return req_id;
end;
$$;
