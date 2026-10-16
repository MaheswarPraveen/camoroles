import os
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

def verify_all_active_jobs():
    """
    Daily liveness checker:
    Probes all active job apply URLs.
    If 404/410/closed, marks is_active = False.
    If healthy, bumps last_verified_at.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in environment.")
        return

    db = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    res = db.table("jobs").select("id, title, company, apply_url").eq("is_active", True).execute()
    jobs = res.data or []

    print(f"[{datetime.now(timezone.utc).isoformat()}] Checking liveness for {len(jobs)} active jobs...")
    active_count = 0
    closed_count = 0

    with httpx.Client(timeout=12.0, follow_redirects=True, headers=HEADERS) as client:
        for job in jobs:
            url = job["apply_url"]
            try:
                r = client.get(url)
                # Check for HTTP errors or common ATS 'Job expired / closed' keywords
                is_closed = False
                if r.status_code in [404, 410]:
                    is_closed = True
                elif r.status_code == 200:
                    body_lower = r.text.lower()
                    if any(term in body_lower for term in [
                        "this job is no longer available",
                        "job has expired",
                        "position has been filled",
                        "no longer accepting applications",
                        "job closed"
                    ]):
                        is_closed = True

                if is_closed:
                    print(f"✖ CLOSED ({r.status_code}): {job['company']} - {job['title']} -> marking inactive")
                    db.table("jobs").update({
                        "is_active": False,
                        "last_verified_at": datetime.now(timezone.utc).isoformat()
                    }).eq("id", job["id"]).execute()
                    closed_count += 1
                else:
                    db.table("jobs").update({
                        "last_verified_at": datetime.now(timezone.utc).isoformat()
                    }).eq("id", job["id"]).execute()
                    active_count += 1

            except Exception as e:
                print(f"⚠ Liveness probe error for {url}: {e}")

    print(f"Liveness check complete. Active: {active_count}, Pruned: {closed_count}")

if __name__ == "__main__":
    verify_all_active_jobs()
