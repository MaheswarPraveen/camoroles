// CamouRoles job agent (Supabase Edge Function, called by pg_cron).
//
//   ?mode=harvest  read the full job list of the 3 least-recently-run company boards:
//                  add new postings, refresh ones still listed, remove ones that left the board.
//   ?mode=check    open the links of jobs that have no board API (direct sites), oldest first;
//                  remove closed ones, refresh live ones. Unclear pages go to the LLM.
//   ?mode=enrich   read the real description of a few new jobs and let the LLM fill
//                  experience range and skills.
//
// Every run writes one row to job_agent_runs so its work can be audited.

import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const AGENT_SECRET = Deno.env.get("JOB_AGENT_SECRET") || "";
const GROQ_API_KEY = Deno.env.get("GROQ_API_KEY") || "";
// Groq free tier: 1,000 requests/day and 8,000 tokens/min per model. The agent only uses a model the
// website does not (site chat/CV use gpt-oss-120b, then qwen), so it never eats into customer calls.
const GROQ_MODELS = ["openai/gpt-oss-20b"];

const db = createClient(SUPABASE_URL, SERVICE_KEY, { auth: { persistSession: false } });

const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36";
const SOURCES_PER_RUN = 3;
const CHECKS_PER_RUN = 40;
const ENRICH_PER_RUN = 1; // every 2 min -> 720 LLM calls/day, under one model's daily cap

type BoardJob = {
  source_key: string;
  title: string;
  company: string;
  ats_type: string;
  location: string;
  is_remote: boolean;
  apply_url: string;
  description: string | null;
  experience_min: number;
  experience_max: number;
  skills: string[];
};

type Source = { id: number; ats: "greenhouse" | "lever" | "ashby"; token: string; company: string; jobs_seen: number | null };

Deno.serve(async (req) => {
  if (!AGENT_SECRET || req.headers.get("x-agent-secret") !== AGENT_SECRET) {
    return json({ error: "forbidden" }, 403);
  }
  const mode = new URL(req.url).searchParams.get("mode") || "harvest";
  try {
    if (mode === "harvest") return json(await runHarvest());
    if (mode === "check") return json(await runCheck());
    if (mode === "enrich") return json(await runEnrich());
    return json({ error: "unknown mode" }, 400);
  } catch (e) {
    await logRun(mode, null, { note: `crash: ${errText(e)}` });
    return json({ error: errText(e) }, 500);
  }
});

// ---------------------------------------------------------------------------
// Harvest: board listing is the source of truth for greenhouse / lever / ashby
// ---------------------------------------------------------------------------
async function runHarvest() {
  const { data: sources, error } = await db
    .from("job_sources")
    .select("id, ats, token, company, jobs_seen")
    .eq("enabled", true)
    .order("last_run_at", { ascending: true, nullsFirst: true })
    .limit(SOURCES_PER_RUN);
  if (error) throw error;

  const results = [];
  for (const src of (sources || []) as Source[]) {
    const label = `${src.ats}:${src.token}`;
    let listing: BoardJob[] | null = null;
    let status = "ok";
    try {
      const raw = await fetchBoard(src);
      const seenKeys = new Set<string>();
      const seenUrls = new Set<string>();
      listing = (raw || []).filter((j) => {
        if (!j.title || seenKeys.has(j.source_key) || seenUrls.has(j.apply_url)) return false;
        seenKeys.add(j.source_key);
        seenUrls.add(j.apply_url);
        return true;
      });
    } catch (e) {
      status = String(e).slice(0, 200);
    }

    if (listing === null) {
      await db.from("job_sources").update({ last_run_at: new Date().toISOString(), last_status: status }).eq("id", src.id);
      await logRun("harvest", label, { note: `board fetch failed: ${status}` });
      results.push({ source: label, error: status });
      continue;
    }

    // An empty list from a board that used to have many jobs is more likely an outage than a mass closure.
    const allowRemove = listing.length > 0 || (src.jobs_seen ?? 0) < 5;
    const { data: applied, error: applyErr } = await db.rpc("job_agent_apply", {
      p_prefix: `${src.ats}:${src.token}:`,
      p_jobs: listing,
      p_allow_remove: allowRemove,
    });
    if (applyErr) {
      // Mark this board as run anyway, so one bad board cannot block the rest of the queue.
      const msg = errText(applyErr);
      await db.from("job_sources").update({ last_run_at: new Date().toISOString(), last_status: `save failed: ${msg}` }).eq("id", src.id);
      await logRun("harvest", label, { note: `save failed: ${msg}` });
      results.push({ source: label, error: msg });
      continue;
    }

    await db.from("job_sources").update({
      last_run_at: new Date().toISOString(),
      last_status: allowRemove ? "ok" : "empty listing, removals skipped",
      jobs_seen: listing.length,
    }).eq("id", src.id);
    await logRun("harvest", label, { ...applied, note: `${listing.length} listed` });
    results.push({ source: label, listed: listing.length, ...applied });
  }
  return { mode: "harvest", results };
}

async function fetchBoard(src: Source): Promise<BoardJob[] | null> {
  if (src.ats === "greenhouse") {
    const res = await fetchWithTimeout(`https://boards-api.greenhouse.io/v1/boards/${src.token}/jobs`, 20000);
    if (res.status === 404) throw new Error("board not found (404)");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const body = await res.json();
    return (body.jobs || []).map((j: any) => boardJob(src, String(j.id), j.title, j.location?.name || "",
      `https://job-boards.greenhouse.io/${src.token}/jobs/${j.id}`, null));
  }

  if (src.ats === "lever") {
    let res = await fetchWithTimeout(`https://api.lever.co/v0/postings/${src.token}?mode=json`, 20000);
    if (res.status === 404) res = await fetchWithTimeout(`https://api.eu.lever.co/v0/postings/${src.token}?mode=json`, 20000);
    if (res.status === 404) throw new Error("board not found (404)");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const body = await res.json();
    if (!Array.isArray(body)) throw new Error("unexpected lever response");
    return body.map((j: any) => {
      const lists = (j.lists || []).map((l: any) => `${l.text}: ${stripHtml(l.content || "")}`).join("\n");
      const desc = `${j.descriptionPlain || ""}\n${lists}`.trim();
      const loc = j.categories?.location || (j.categories?.allLocations || []).join(", ") || "";
      const job = boardJob(src, String(j.id).toLowerCase(), j.text, loc, j.hostedUrl, desc);
      if (j.workplaceType === "remote") job.is_remote = true;
      return job;
    });
  }

  // ashby
  const res = await fetchWithTimeout(`https://api.ashbyhq.com/posting-api/job-board/${src.token}`, 20000);
  if (res.status === 404) throw new Error("board not found (404)");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const body = await res.json();
  return (body.jobs || [])
    .filter((j: any) => j.isListed !== false)
    .map((j: any) => {
      const job = boardJob(src, String(j.id).toLowerCase(), j.title, j.location || "",
        j.jobUrl || `https://jobs.ashbyhq.com/${src.token}/${j.id}`, j.descriptionPlain || null);
      // Ashby sets isRemote on hybrid roles too, so trust workplaceType when it is present.
      if (j.workplaceType ? j.workplaceType === "Remote" : j.isRemote) job.is_remote = true;
      return job;
    });
}

function boardJob(src: Source, id: string, title: string, location: string, url: string, description: string | null): BoardJob {
  const exp = guessExperience(title);
  return {
    source_key: `${src.ats}:${src.token}:${id}`,
    title: String(title || "").trim().slice(0, 300),
    company: src.company,
    ats_type: src.ats,
    location: String(location || "").trim().slice(0, 200),
    is_remote: /\b(remote|anywhere|distributed)\b/i.test(location || ""),
    apply_url: url,
    description: description ? description.slice(0, 6000) : null,
    experience_min: exp[0],
    experience_max: exp[1],
    skills: [],
  };
}

// Placeholder until the enrich step reads the description.
function guessExperience(title: string): [number, number] {
  const t = ` ${String(title || "").toLowerCase()} `;
  if (/\b(intern|internship|new grad|graduate|trainee|apprentice)\b/.test(t)) return [0, 1];
  if (/\b(principal|staff|director|head of|vp|distinguished)\b/.test(t)) return [8, 15];
  if (/\b(senior|sr\.?|lead|iii)\b/.test(t)) return [5, 9];
  if (/\b(junior|jr\.?|associate|entry|early career)\b|\bi\b|\b1\b/.test(t)) return [0, 2];
  if (/\bii\b|\b2\b/.test(t)) return [2, 5];
  return [2, 6];
}

// ---------------------------------------------------------------------------
// Check: jobs without a board API (direct company sites, LinkedIn, etc.)
// ---------------------------------------------------------------------------
const CLOSED_PHRASES = [
  "no longer available", "position has been filled", "no longer accepting applications", "job has expired",
  "requisition is closed", "posting has closed", "opening is closed", "has been filled", "job not found",
  "posting has expired", "this job is closed", "job is no longer open", "page you are looking for doesn't exist",
];
const UNCLEAR_PHRASES = ["talent community", "talent pool", "future openings", "check back soon", "join our talent network"];

async function runCheck() {
  const { data: jobs, error } = await db
    .from("jobs")
    .select("id, title, company, apply_url")
    .eq("is_active", true)
    .is("source_key", null)
    .order("last_checked_at", { ascending: true, nullsFirst: true })
    .limit(CHECKS_PER_RUN);
  if (error) throw error;

  const verdicts = await mapLimit(jobs || [], 8, (j: any) => checkLink(j));
  const live = verdicts.filter((v) => v.verdict === "live").map((v) => v.id);
  const closed = verdicts.filter((v) => v.verdict === "closed").map((v) => v.id);
  const unknown = verdicts.filter((v) => v.verdict === "unknown");
  const now = new Date().toISOString();

  if (live.length) await db.from("jobs").update({ last_verified_at: now, last_checked_at: now }).in("id", live);
  if (closed.length) await db.from("jobs").update({ is_active: false, last_verified_at: now, last_checked_at: now }).in("id", closed);
  // Unknown (blocked, timeout, 5xx): leave last_verified_at alone so the 14-day rule retires
  // links that stay unreachable, but move them to the back of the queue.
  if (unknown.length) await db.from("jobs").update({ last_checked_at: now }).in("id", unknown.map((u) => u.id));
  const reasons = unknown.slice(0, 5).map((u) => u.reason).join("; ");
  await logRun("check", null, { refreshed: live.length, removed: closed.length, note: `${unknown.length} unknown${reasons ? ` (${reasons})` : ""}` });
  return { mode: "check", checked: verdicts.length, live: live.length, closed: closed.length, unknown: unknown.length };
}

async function checkLink(job: { id: string; title: string; company: string; apply_url: string }) {
  const url = String(job.apply_url || "");
  if (!/^https?:\/\//.test(url)) return { id: job.id, verdict: "closed", reason: "no url" };
  try {
    const res = await fetchWithTimeout(url, 12000, { headers: { "User-Agent": UA, "Accept": "text/html,*/*" } });
    if (res.status === 404 || res.status === 410) return { id: job.id, verdict: "closed", reason: `HTTP ${res.status}` };
    if (!res.ok) return { id: job.id, verdict: "unknown", reason: `HTTP ${res.status}` };
    const html = (await res.text()).slice(0, 400000);
    const text = stripHtml(html).toLowerCase();
    if (CLOSED_PHRASES.some((p) => text.includes(p))) return { id: job.id, verdict: "closed", reason: "closed notice" };
    if (redirectedToListing(url, res.url)) return { id: job.id, verdict: "closed", reason: "redirected to careers home" };
    if (UNCLEAR_PHRASES.some((p) => text.includes(p))) {
      const closedByLlm = await askLlmIfClosed(job.title, job.company, text);
      if (closedByLlm === true) return { id: job.id, verdict: "closed", reason: "llm: closed" };
      if (closedByLlm === null) return { id: job.id, verdict: "unknown", reason: "llm unavailable" };
    }
    return { id: job.id, verdict: "live", reason: "ok" };
  } catch (e) {
    return { id: job.id, verdict: "unknown", reason: String(e).slice(0, 60) };
  }
}

function redirectedToListing(original: string, final: string) {
  if (!final || final === original) return false;
  const clean = (u: string) => u.split("#")[0].split("?")[0].replace(/\/+$/, "");
  const a = clean(original), b = clean(final);
  if (a === b) return false;
  return /\/(careers|jobs|open-roles|join-us|positions)$/i.test(b) || b.split("/").length < a.split("/").length - 1;
}

async function askLlmIfClosed(title: string, company: string, pageText: string): Promise<boolean | null> {
  const out = await groqJson([
    { role: "system", content: 'You check job pages. Reply only with JSON {"is_closed": boolean}. Closed means the page says the role is filled/expired, or it is only a generic talent pool page without this role.' },
    { role: "user", content: `Role: ${title}\nCompany: ${company}\nPage text:\n${pageText.slice(0, 2500)}` },
  ], 40);
  return out && typeof out.is_closed === "boolean" ? out.is_closed : null;
}

// ---------------------------------------------------------------------------
// Enrich: real experience range and skills from the job description
// ---------------------------------------------------------------------------
async function runEnrich() {
  if (!GROQ_API_KEY) return { mode: "enrich", skipped: "no GROQ_API_KEY" };
  const { data: jobs, error } = await db
    .from("jobs")
    .select("id, title, company, description, source_key, apply_url")
    .eq("is_active", true)
    .is("enriched_at", null)
    .order("created_at", { ascending: false })
    .limit(ENRICH_PER_RUN);
  if (error) throw error;

  let enriched = 0;
  const notes: string[] = [];
  for (const job of jobs || []) {
    let desc = job.description && job.description.length > 200 && !job.description.startsWith("Verified active technical requisition")
      ? job.description
      : await fetchDescription(job.source_key, job.apply_url);
    if (!desc || desc.length < 200) {
      // Nothing to read; mark it so the queue moves on.
      await db.from("jobs").update({ enriched_at: new Date().toISOString() }).eq("id", job.id);
      notes.push(`no description: ${job.title}`);
      continue;
    }
    desc = desc.slice(0, 5000);
    const out = await groqJson([
      {
        role: "system",
        content: "You read job descriptions. Reply only with JSON: " +
          '{"experience_min": int, "experience_max": int, "skills": [up to 8 short skill names], "is_remote": boolean}. ' +
          "Use the years of experience the description asks for; if it gives none, infer from the seniority of the title. " +
          "Skills must appear in or be clearly required by the description.",
      },
      { role: "user", content: `Title: ${job.title}\nCompany: ${job.company}\n\n${desc}` },
    ], 200);
    if (!out) {
      notes.push("llm unavailable");
      break; // rate-limited: stop and let the next run continue
    }
    const min = clampInt(out.experience_min, 0, 25, 0);
    const max = Math.max(min, clampInt(out.experience_max, 0, 30, min + 3));
    const skills = Array.isArray(out.skills) ? out.skills.map((s: unknown) => String(s).trim()).filter(Boolean).slice(0, 8) : [];
    const update: Record<string, unknown> = {
      experience_min: min,
      experience_max: max,
      skills,
      description: desc,
      enriched_at: new Date().toISOString(),
    };
    if (out.is_remote === true) update.is_remote = true;
    await db.from("jobs").update(update).eq("id", job.id);
    enriched++;
  }
  await logRun("enrich", null, { enriched, note: notes.join("; ").slice(0, 300) || null });
  return { mode: "enrich", enriched, notes };
}

async function fetchDescription(sourceKey: string | null, applyUrl: string): Promise<string | null> {
  try {
    if (sourceKey?.startsWith("greenhouse:")) {
      const [, token, id] = sourceKey.split(":");
      const res = await fetchWithTimeout(`https://boards-api.greenhouse.io/v1/boards/${token}/jobs/${id}`, 12000);
      if (!res.ok) return null;
      const body = await res.json();
      return stripHtml(decodeEntities(body.content || ""));
    }
    const res = await fetchWithTimeout(applyUrl, 12000, { headers: { "User-Agent": UA } });
    if (!res.ok) return null;
    return stripHtml((await res.text()).slice(0, 400000));
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------
async function groqJson(messages: { role: string; content: string }[], maxTokens: number): Promise<any | null> {
  if (!GROQ_API_KEY) return null;
  for (const model of GROQ_MODELS) {
    try {
      const res = await fetchWithTimeout("https://api.groq.com/openai/v1/chat/completions", 20000, {
        method: "POST",
        headers: { "Authorization": `Bearer ${GROQ_API_KEY}`, "Content-Type": "application/json" },
        // Both models reason before answering; low effort keeps that short, and the token budget leaves room for it.
        body: JSON.stringify({
          model, messages, temperature: 0, max_tokens: maxTokens + 400, reasoning_effort: "low",
          response_format: { type: "json_object" },
        }),
      });
      if (!res.ok) continue;
      const body = await res.json();
      return JSON.parse(body.choices?.[0]?.message?.content || "null");
    } catch {
      // try the next model
    }
  }
  return null;
}

async function fetchWithTimeout(url: string, ms: number, init: RequestInit = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), ms);
  try {
    return await fetch(url, { redirect: "follow", ...init, signal: ctrl.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function mapLimit<T, R>(items: T[], limit: number, fn: (item: T) => Promise<R>): Promise<R[]> {
  const out: R[] = new Array(items.length);
  let next = 0;
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (next < items.length) {
      const i = next++;
      out[i] = await fn(items[i]);
    }
  }));
  return out;
}

function stripHtml(html: string) {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function decodeEntities(s: string) {
  return s.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, "&");
}

function clampInt(v: unknown, lo: number, hi: number, fallback: number) {
  const n = Math.round(Number(v));
  return Number.isFinite(n) ? Math.min(hi, Math.max(lo, n)) : fallback;
}

async function logRun(mode: string, source: string | null, r: { added?: number; removed?: number; refreshed?: number; enriched?: number; note?: string | null }) {
  await db.from("job_agent_runs").insert({
    mode,
    source,
    added: r.added || 0,
    removed: r.removed || 0,
    refreshed: r.refreshed || 0,
    enriched: r.enriched || 0,
    note: r.note || null,
  });
}

// Supabase errors are plain objects, so String(e) only gives "[object Object]".
function errText(e: any) {
  const msg = e?.message ? `${e.code ? e.code + " " : ""}${e.message}` : String(e);
  return msg.slice(0, 300);
}

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json" } });
}
