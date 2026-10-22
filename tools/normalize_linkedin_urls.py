import os
import re
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("backend/.env")
load_dotenv(".env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
sb = create_client(url, key)

res = sb.table("jobs").select("id,apply_url").ilike("apply_url", "%linkedin%").execute()
updated = 0
for j in res.data or []:
    raw = j["apply_url"]
    m = re.search(r'(\d{8,})', raw)
    if m:
        job_id = m.group(1)
        clean = f"https://www.linkedin.com/jobs/view/{job_id}?trk=public_jobs_topcard-title"
        if clean != raw:
            sb.table("jobs").update({"apply_url": clean}).eq("id", j["id"]).execute()
            updated += 1

print(f"Normalized {updated} LinkedIn job URLs to direct public viewing format.")
