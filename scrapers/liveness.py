import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv

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

    db_headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }

    jobs_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/jobs?is_active=eq.true&select=id,title,company,apply_url"
    r = httpx.get(jobs_url, headers=db_headers, timeout=15.0)
    jobs = r.json() if r.status_code == 200 else []

    print(f"[{datetime.now(timezone.utc).isoformat()}] Checking liveness for {len(jobs)} active jobs...")
    active_count = 0
    closed_count = 0

    with httpx.Client(timeout=12.0, follow_redirects=True, headers=HEADERS) as client:
        for job in jobs:
            url = job["apply_url"]
            try:
                res = client.get(url)
                is_closed = False
                if res.status_code in [404, 410]:
                    is_closed = True
                elif res.status_code == 200:
                    body_lower = res.text.lower()
                    if any(term in body_lower for term in [
                        "this job is no longer available",
                        "job has expired",
                        "position has been filled",
                        "no longer accepting applications",
                        "job closed"
                    ]):
                        is_closed = True

                patch_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/jobs?id=eq.{job['id']}"
                if is_closed:
                    print(f"✖ CLOSED: {job['company']} - {job['title']} -> marked inactive")
                    httpx.patch(patch_url, headers=db_headers, json={
                        "is_active": False,
                        "last_verified_at": datetime.now(timezone.utc).isoformat()
                    })
                    closed_count += 1
                else:
                    httpx.patch(patch_url, headers=db_headers, json={
                        "last_verified_at": datetime.now(timezone.utc).isoformat()
                    })
                    active_count += 1

            except Exception as e:
                print(f"⚠ Liveness probe error for {url}: {e}")

    print(f"Liveness check complete. Active: {active_count}, Pruned: {closed_count}")

if __name__ == "__main__":
    verify_all_active_jobs()
