import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from typing import Dict, Any, List
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

class ATSIngestor:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured in .env")
        self.endpoint = f"{SUPABASE_URL.rstrip('/')}/rest/v1/jobs?on_conflict=apply_url"
        self.headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        self.client = httpx.Client(timeout=15.0)

    def ingest_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Upserts a job role directly into Supabase via high-speed PostgREST:
        - Resolves duplicate URLs automatically
        - Updates is_active and verified date
        """
        apply_url = str(job_data.get("apply_url", "")).strip()
        if not apply_url:
            return False

        # Attempt embedding generation if fastembed is present
        emb = None
        try:
            from backend.embeddings import generate_embedding
            emb_input = f"{job_data.get('title', '')} at {job_data.get('company', '')}. Location: {job_data.get('location', '')}. Required Skills: {', '.join(job_data.get('skills', []))}."
            emb = generate_embedding(emb_input)
        except Exception:
            emb = None

        row = {
            "title": str(job_data.get("title", "")).strip(),
            "company": str(job_data.get("company", "")).strip(),
            "ats_type": str(job_data.get("ats_type", "direct")),
            "location": str(job_data.get("location", "Remote / Worldwide")).strip(),
            "is_remote": bool(job_data.get("is_remote", False)),
            "experience_min": int(job_data.get("experience_min", 0)),
            "experience_max": int(job_data.get("experience_max", 3)),
            "apply_url": apply_url,
            "description": str(job_data.get("description", "")).strip(),
            "skills": list(job_data.get("skills", [])),
            "is_active": True
        }
        if emb is not None:
            row["embedding"] = emb

        try:
            r = self.client.post(self.endpoint, headers=self.headers, json=row)
            if r.status_code in (200, 201, 204):
                return True
            else:
                return False
        except Exception as e:
            return False

    def batch_ingest_jobs(self, jobs_data: List[Dict[str, Any]]) -> int:
        """Batch upserts multiple jobs at high speed into Supabase."""
        if not jobs_data:
            return 0

        rows = []
        for j in jobs_data:
            url = str(j.get("apply_url", "")).strip()
            if not url:
                continue
            rows.append({
                "title": str(j.get("title", "")).strip(),
                "company": str(j.get("company", "")).strip(),
                "ats_type": str(j.get("ats_type", "direct")),
                "location": str(j.get("location", "Remote / Worldwide")).strip(),
                "is_remote": bool(j.get("is_remote", False)),
                "experience_min": int(j.get("experience_min", 0)),
                "experience_max": int(j.get("experience_max", 3)),
                "apply_url": url,
                "description": str(j.get("description", "")).strip(),
                "skills": list(j.get("skills", [])),
                "is_active": True
            })

        inserted = 0
        batch_size = 50
        for i in range(0, len(rows), batch_size):
            chunk = rows[i:i + batch_size]
            try:
                r = self.client.post(self.endpoint, headers=self.headers, json=chunk)
                if r.status_code in (200, 201, 204):
                    inserted += len(chunk)
                    print(f"[OK] Batch ingested {len(chunk)} jobs (progress: {inserted}/{len(rows)})")
                else:
                    # Fallback to item-by-item on batch conflict
                    for item in chunk:
                        if self.ingest_job(item):
                            inserted += 1
            except Exception as e:
                for item in chunk:
                    if self.ingest_job(item):
                        inserted += 1

        return inserted
