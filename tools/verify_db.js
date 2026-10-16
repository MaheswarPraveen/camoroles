const fs = require('fs');

const env = Object.fromEntries(
  fs.readFileSync('supabase.env', 'utf8')
    .split(/\r?\n/)
    .filter((l) => /^[A-Z_]+=/.test(l))
    .map((l) => [l.split('=')[0], l.slice(l.indexOf('=') + 1).trim()])
);

async function check() {
  const query = `
    select table_name 
    from information_schema.tables 
    where table_schema = 'public' 
      and table_name in ('jobs', 'cv_profiles', 'job_matches', 'user_entitlements', 'job_orders');
  `;
  const res = await fetch('https://api.supabase.com/v1/projects/xteoktfzftqybflpubvo/database/query', {
    method: 'POST',
    headers: {
      Authorization: 'Bearer ' + env.SUPABASE_ACCESS_TOKEN,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query })
  });
  console.log("Tables in database:", await res.json());

  // Also verify pg_cron jobs
  const cronQuery = `select jobid, jobname, schedule, active from cron.job;`;
  const cronRes = await fetch('https://api.supabase.com/v1/projects/xteoktfzftqybflpubvo/database/query', {
    method: 'POST',
    headers: {
      Authorization: 'Bearer ' + env.SUPABASE_ACCESS_TOKEN,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query: cronQuery })
  });
  console.log("Active pg_cron schedules:", await cronRes.json());
}

check();
