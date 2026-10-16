import os
import sys
import concurrent.futures
from typing import Dict, Any, List
import httpx
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Missing Supabase credentials in .env")
    sys.exit(1)

db = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def check_url(job: Dict[str, Any]) -> Dict[str, Any]:
    url = job.get("apply_url", "").strip()
    job_id = job.get("id")
    company = job.get("company", "")
    title = job.get("title", "")

    if not url or not url.startswith("http"):
        return {"id": job_id, "company": company, "title": title, "url": url, "valid": False, "status": 0, "reason": "invalid_url"}

    # Immediate purge for known synthetic seeded fake domains
    if any(fake_pattern in url for fake_pattern in ["jobs.apple.com/en-us/details/200591", "metacareers.com/jobs/83918204", "careers.microsoft.com/us/en/job/1749", "nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite/job/USA-CA-Santa-Clara/Robotics", "sony.wd1.myworkdayjobs.com/SonyCareers/job/Tokyo/Autonomous", "uber.com/global/en/careers/list/129841", "amazon.jobs/en/jobs/2718942", "google.com/about/careers/applications/jobs/results/148920194", "tesla.com/careers/search/job/robotics-engineer-optimus-218491"]):
        return {"id": job_id, "company": company, "title": title, "url": url, "valid": False, "status": 404, "reason": "synthetic_seed"}

    try:
        # Use httpx with follow_redirects
        with httpx.Client(timeout=8.0, headers=HEADERS, follow_redirects=True, verify=False) as client:
            resp = client.get(url)
            status = resp.status_code
            final_url = str(resp.url)

            # Check if status is 200 or 3xx
            if status == 200:
                # Also check if it redirected to a generic 404 page or generic careers homepage without the job
                text_lower = resp.text[:2000].lower()
                if "job not found" in text_lower or "position no longer available" in text_lower or "page not found" in text_lower or "404" in resp.headers.get("title", "").lower():
                    return {"id": job_id, "company": company, "title": title, "url": url, "valid": False, "status": 404, "reason": "job_closed"}
                return {"id": job_id, "company": company, "title": title, "url": url, "valid": True, "status": 200, "final_url": final_url}
            elif status in (404, 410, 403, 500, 502, 503):
                return {"id": job_id, "company": company, "title": title, "url": url, "valid": False, "status": status, "reason": f"http_{status}"}
            else:
                return {"id": job_id, "company": company, "title": title, "url": url, "valid": False, "status": status, "reason": f"http_{status}"}
    except Exception as e:
        return {"id": job_id, "company": company, "title": title, "url": url, "valid": False, "status": 0, "reason": str(e)[:60]}

def main():
    print("Fetching all jobs from Supabase...")
    res = db.table("jobs").select("id, company, title, apply_url, ats_type, is_active").execute()
    jobs = res.data or []
    print(f"Total jobs to verify: {len(jobs)}")

    valid_jobs = []
    broken_jobs = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_to_job = {executor.submit(check_url, j): j for j in jobs}
        for future in concurrent.futures.as_completed(future_to_job):
            result = future.result()
            if result["valid"]:
                valid_jobs.append(result)
                print(f"[OK 200] {result['company']} - {result['title'][:35]} -> {result['url'][:60]}")
            else:
                broken_jobs.append(result)
                print(f"[BROKEN {result['status']}] {result['company']} - {result['title'][:35]} ({result['reason']})")

    print("\n" + "="*60)
    print(f"VERIFICATION SUMMARY:")
    print(f"Total checked: {len(jobs)}")
    print(f"Working Verified: {len(valid_jobs)}")
    print(f"Broken / Dead: {len(broken_jobs)}")
    print("="*60)

    # Delete or deactivate broken jobs
    if broken_jobs:
        broken_ids = [b["id"] for b in broken_jobs]
        print(f"Purging {len(broken_ids)} broken/dead jobs from Supabase...")
        batch_size = 50
        for i in range(0, len(broken_ids), batch_size):
            chunk = broken_ids[i:i+batch_size]
            db.table("jobs").delete().in_("id", chunk).execute()
        print("Purge complete!")

    print(f"Remaining 100% verified live jobs in database: {len(valid_jobs)}")

if __name__ == "__main__":
    main()
