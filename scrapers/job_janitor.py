"""
Job Janitor Agent: Autonomous Dead Link & Stale Requisition Pruning Engine.
Uses a 3-tier verification pipeline:
1. HTTP status code inspection (404, 410, domain redirects)
2. High-precision deterministic closure heuristics
3. Qwen (via Groq JSON mode) reasoning for ambiguous soft-closures
"""

import os
import sys
import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

CLOSURE_PHRASES = [
    "this job is no longer available",
    "position has been filled",
    "no longer accepting applications",
    "this position has been filled",
    "job has expired",
    "this requisition is closed",
    "this job posting has closed",
    "this opening is closed",
    "the role you are looking for has been filled",
    "job not found",
    "posting has expired"
]

class JobJanitorAgent:
    def __init__(self, concurrency: int = 25):
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required in .env")
        
        self.db_headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json"
        }
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)

    async def fetch_batch_to_verify(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Fetch the oldest verified or never-verified active jobs from Supabase."""
        url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/jobs?is_active=eq.true&order=last_verified_at.asc.nullsfirst&limit={limit}&select=id,title,company,apply_url,ats_type"
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url, headers=self.db_headers)
            if r.status_code == 200:
                return r.json()
            return []

    async def ask_qwen_closure_reasoning(self, title: str, company: str, page_snippet: str) -> bool:
        """
        Tier 3 reasoning: If the page returns 200 OK but has suspicious text or redirect,
        use Qwen (via Groq JSON mode) to determine if this job is actively open or closed.
        Returns True if CLOSED, False if OPEN.
        """
        if not GROQ_API_KEY:
            return False

        clean_snippet = re.sub(r'\s+', ' ', page_snippet[:1500]).strip()
        system_prompt = (
            "You are an expert ATS auditor analyzing whether a specific job listing is still open and accepting applications.\n"
            "Given the job title, company, and raw page text snippet, determine if the position is CLOSED (expired, filled, paused, or redirected to a generic talent pool/homepage) "
            "or ACTIVE (has an application form or explicit open requisition).\n"
            "Respond ONLY with a JSON object:\n"
            '{\n  "is_closed": boolean,\n  "reason": "1-sentence explanation"\n}'
        )

        user_content = f"Company: {company}\nTarget Role: {title}\nPage Snippet:\n{clean_snippet}"
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                    json={
                        "model": "qwen/qwen3.8-27b",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content}
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.1,
                        "max_tokens": 120
                    }
                )
                if res.status_code == 200:
                    data = res.json()["choices"][0]["message"]["content"]
                    parsed = json.loads(data)
                    return bool(parsed.get("is_closed", False))
        except Exception:
            pass
        return False

    async def verify_single_job(self, client: httpx.AsyncClient, job: Dict[str, Any]) -> Dict[str, Any]:
        """Probes a single job's apply URL across all 3 tiers."""
        jid = job["id"]
        title = job.get("title", "")
        company = job.get("company", "")
        url = str(job.get("apply_url", "")).strip()

        if not url or not url.startswith("http"):
            return {"id": jid, "status": "closed", "reason": "Invalid or missing URL"}

        async with self.semaphore:
            try:
                res = await client.get(url, headers=HEADERS, timeout=9.0, follow_redirects=True)
                final_url = str(res.url)

                # Tier 1: Definite HTTP status codes
                if res.status_code in [404, 410]:
                    return {"id": jid, "status": "closed", "reason": f"HTTP {res.status_code}"}
                
                # Check for stealth redirects away from specific job posting (e.g. redirected to /careers or /careers#open-positions)
                is_redirected_to_root = False
                if final_url != url:
                    clean_final = final_url.split("#")[0].split("?")[0].rstrip("/")
                    clean_orig = url.split("#")[0].split("?")[0].rstrip("/")
                    if ("/jobs/" in clean_orig and "/jobs/" not in clean_final) or ("/postings/" in clean_orig and "/postings/" not in clean_final):
                        is_redirected_to_root = True
                    elif any(clean_final.endswith(x) for x in ["/careers", "/jobs", "/boards", "/join-us", "/open-roles"]):
                        is_redirected_to_root = True

                # Tier 2: Deterministic text heuristics
                body_lower = res.text.lower()
                for phrase in CLOSURE_PHRASES:
                    if phrase in body_lower:
                        return {"id": jid, "status": "closed", "reason": f"Closure notice: '{phrase}'"}

                if is_redirected_to_root:
                    return {"id": jid, "status": "closed", "reason": "Redirected to root careers board"}

                # Tier 3: Ambiguous redirect or suspicious landing -> Qwen reasoning
                suspicious_terms = ["talent community", "talent pool", "future openings", "reviewing applications", "check back soon"]
                if any(st in body_lower for st in suspicious_terms) or (res.status_code != 200):
                    is_closed = await self.ask_qwen_closure_reasoning(title, company, res.text)
                    if is_closed:
                        return {"id": jid, "status": "closed", "reason": "Qwen identified closed/talent-pool state"}

                # Healthy live job
                return {"id": jid, "status": "active", "reason": "Verified active"}

            except httpx.HTTPStatusError as e:
                if e.response.status_code in [404, 410]:
                    return {"id": jid, "status": "closed", "reason": f"HTTP {e.response.status_code}"}
                return {"id": jid, "status": "active", "reason": f"HTTP {e.response.status_code} tolerated"}
            except Exception as e:
                # Network timeouts are marked active to avoid accidental pruning on temporary glitches
                return {"id": jid, "status": "active", "reason": f"Probe error tolerated: {type(e).__name__}"}

    async def run_janitor_sweep(self, limit: int = 150) -> Dict[str, Any]:
        """Runs an autonomous verification sweep over the target batch."""
        jobs = await self.fetch_batch_to_verify(limit=limit)
        if not jobs:
            print("[Job Janitor] No active jobs found to verify.")
            return {"total": 0, "active": 0, "pruned": 0}

        print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Job Janitor sweep started for {len(jobs)} positions...")
        start_time = asyncio.get_event_loop().time()

        active_ids = []
        closed_records = []

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as probe_client:
            tasks = [self.verify_single_job(probe_client, j) for j in jobs]
            results = await asyncio.gather(*tasks)

        now_iso = datetime.now(timezone.utc).isoformat()
        async with httpx.AsyncClient(timeout=15.0) as patch_client:
            for res in results:
                jid = res["id"]
                if res["status"] == "closed":
                    closed_records.append(res)
                    patch_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/jobs?id=eq.{jid}"
                    await patch_client.patch(patch_url, headers=self.db_headers, json={
                        "is_active": False,
                        "last_verified_at": now_iso
                    })
                else:
                    active_ids.append(jid)
                    patch_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/jobs?id=eq.{jid}"
                    await patch_client.patch(patch_url, headers=self.db_headers, json={
                        "last_verified_at": now_iso
                    })

        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"[Job Janitor Sweep Complete] Total: {len(jobs)} | Verified Active: {len(active_ids)} | Pruned/Closed: {len(closed_records)} | Time: {elapsed:.2f}s")
        if closed_records:
            print(f"  Sample pruned: {closed_records[0]['reason']}")

        return {
            "total": len(jobs),
            "active": len(active_ids),
            "pruned": len(closed_records),
            "elapsed_seconds": round(elapsed, 2)
        }

if __name__ == "__main__":
    janitor = JobJanitorAgent(concurrency=20)
    asyncio.run(janitor.run_janitor_sweep(limit=50))
