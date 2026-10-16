import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from supabase import create_client
from backend.embeddings import generate_embedding

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

class ATSIngestor:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured in .env")
        self.db = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    def ingest_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Upserts a job role into the database:
        - Computes embedding from title + skills + description
        - Ignores or updates on conflict (apply_url)
        """
        apply_url = job_data.get("apply_url", "").strip()
        if not apply_url:
            return False

        # Generate dense text representation for embedding
        embedding_input = f"{job_data.get('title', '')} at {job_data.get('company', '')}. Location: {job_data.get('location', '')}. Required Skills: {', '.join(job_data.get('skills', []))}. Summary: {job_data.get('description', '')[:500]}"
        
        try:
            emb = generate_embedding(embedding_input)
        except Exception as e:
            print(f"Embedding generation skipped for {job_data.get('title')}: {e}")
            emb = None

        row = {
            "title": job_data.get("title", "").strip(),
            "company": job_data.get("company", "").strip(),
            "ats_type": job_data.get("ats_type", "direct"),
            "location": job_data.get("location", "India").strip(),
            "is_remote": bool(job_data.get("is_remote", False)),
            "experience_min": int(job_data.get("experience_min", 0)),
            "experience_max": int(job_data.get("experience_max", 3)),
            "apply_url": apply_url,
            "description": job_data.get("description", "").strip(),
            "skills": job_data.get("skills", []),
            "embedding": emb,
            "is_active": True
        }

        try:
            self.db.table("jobs").upsert(row, on_conflict="apply_url").execute()
            print(f"✓ Ingested: {row['company']} - {row['title']} ({row['location']})")
            return True
        except Exception as e:
            print(f"✖ Failed to upsert job {apply_url}: {e}")
            return False
