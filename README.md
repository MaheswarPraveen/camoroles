# camOroles.in (Jobinator) - Hidden Job Matcher for India

> "Hidden jobs LinkedIn doesn't show you." 
> Instant CV matching to niche Indian startup & tech career pages (Keka, Darwinbox, Zoho Recruit, unlisted direct boards).

---

## 1. System Architecture

```
[ ATS Career Pages (Keka, Darwinbox, Zoho) ]
                    │
           Python Scraper Engine
                    │
         Liveness & Extraction Pipeline
                    ▼
     Postgres + pgvector (`jobs` table)
                    ▲
                    │ 1. Vector Candidate Retrieval (Top N)
                    │ 2. Groq LLM Score + 2-line Rationale (Cached)
                    │
   [ Web App / Landing Page (Cloudflare + Edge) ]
           ▲                          ▲
           │ Free Previews            │ CV Upload (In-Memory Text & Embedding)
           │                          │ (Raw PDF is never stored - DPDP compliant)
     [ Guest Visitors ]          [ Job Seekers ]
```

---

## 2. Core Principles & Guardrails

1. **Zero PDF Storage**:
   - Resumes are parsed in-memory, converted to text summary + vector embedding, and discarded immediately.
   - Complies with India's Digital Personal Data Protection (DPDP) Act.
2. **Deterministic & Cached Scoring**:
   - Vector similarity filters candidates in Postgres via `pgvector`.
   - Top candidates get a 1-shot LLM rubric evaluation for exact match score (1–100) + 2-line "why it matches".
   - The result is cached in `job_matches(user_id, job_id)` permanently. It is **never** re-evaluated on subsequent visits.
3. **No Phantom Jobs**:
   - Daily liveness checker (`HEAD`/`GET` HTTP probes) marks closed postings as inactive.
   - Every role displays a "Verified Active: [X] hours ago" badge.
4. **Simple, Frictionless Pricing**:
   - Razorpay one-time checkout (no recurring auto-debit).
   - ₹30 / week (unlimited links + alerts)
   - ₹100 / month (unlimited links + agent chat + alerts)
   - Free tier: 3 apply link unlocks per week.

---

## 3. Directory Layout

- `scrapers/`: ATS scrapers (Keka, Darwinbox, Zoho Recruit) and URL liveness validator.
- `supabase/migrations/`: Postgres schemas, `pgvector` configuration, RLS policies, and match caching tables.
- `backend/`: Fast API / Edge functions for CV text extraction, embedding generation, and match scoring.
- `web/`: High-converting landing page with hidden-company teaser preview and job seeker dashboard.
- `tools/`: Ops, backup, token usage tracking, and match quality evaluation harness.
