-- Schedules for the job agent edge function. Replace <JOB_AGENT_SECRET> before running.
-- harvest: 3 boards every 10 min -> every board re-read about every 4-5 hours
-- check:   40 direct links every 10 min (each run hits different sites)
-- enrich:  1 new job every 2 min -> 720 Groq calls/day (free cap is 1,000/day per model)

select cron.unschedule(jobname) from cron.job where jobname in ('job-agent-harvest', 'job-agent-check', 'job-agent-enrich');

select cron.schedule('job-agent-harvest', '*/10 * * * *', $$
  select net.http_post(
    url := 'https://xteoktfzftqybflpubvo.supabase.co/functions/v1/job-agent?mode=harvest',
    headers := jsonb_build_object('Content-Type', 'application/json', 'x-agent-secret', '<JOB_AGENT_SECRET>'),
    body := '{}'::jsonb,
    timeout_milliseconds := 150000
  );
$$);

select cron.schedule('job-agent-check', '2-59/10 * * * *', $$
  select net.http_post(
    url := 'https://xteoktfzftqybflpubvo.supabase.co/functions/v1/job-agent?mode=check',
    headers := jsonb_build_object('Content-Type', 'application/json', 'x-agent-secret', '<JOB_AGENT_SECRET>'),
    body := '{}'::jsonb,
    timeout_milliseconds := 150000
  );
$$);

select cron.schedule('job-agent-enrich', '1-59/2 * * * *', $$
  select net.http_post(
    url := 'https://xteoktfzftqybflpubvo.supabase.co/functions/v1/job-agent?mode=enrich',
    headers := jsonb_build_object('Content-Type', 'application/json', 'x-agent-secret', '<JOB_AGENT_SECRET>'),
    body := '{}'::jsonb,
    timeout_milliseconds := 150000
  );
$$);
