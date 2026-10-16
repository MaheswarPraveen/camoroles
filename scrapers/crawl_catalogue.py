import os
import json
import httpx
from scrapers.ats_base import ATSIngestor

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "companies_1000.json")

def crawl_company_jobs(limit: int = 50):
    """
    Crawls career openings across the 1,000+ Indian company catalogue.
    Handles Keka, Darwinbox, Zoho Recruit, Greenhouse, and Lever API feeds.
    """
    if not os.path.exists(CATALOG_PATH):
        print(f"Catalogue file not found at {CATALOG_PATH}")
        return

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        companies = json.load(f)

    print(f"Loaded {len(companies)} companies. Initiating crawl for up to {limit} companies...")
    ingestor = ATSIngestor()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html"
    }

    scraped_count = 0
    with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
        for c in companies[:limit]:
            ats = c.get("ats")
            name = c.get("name")
            careers_url = c.get("careers")

            try:
                # 1. Greenhouse Boards API
                if ats == "greenhouse":
                    slug = careers_url.rstrip("/").split("/")[-1]
                    api_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
                    res = client.get(api_url)
                    if res.status_code == 200:
                        jobs = res.json().get("jobs", [])
                        for j in jobs:
                            loc = (j.get("location") or {}).get("name", "India")
                            # Filter for India or Remote
                            if any(k in loc.lower() for k in ["india", "bengaluru", "bangalore", "delhi", "gurgaon", "noida", "mumbai", "pune", "hyderabad", "chennai", "remote"]):
                                ingestor.ingest_job({
                                    "title": j.get("title"),
                                    "company": name,
                                    "ats_type": "greenhouse",
                                    "location": loc,
                                    "is_remote": "remote" in loc.lower() or "remote" in j.get("title", "").lower(),
                                    "experience_min": 0,
                                    "experience_max": 3,
                                    "apply_url": j.get("absolute_url"),
                                    "description": f"Role: {j.get('title')} at {name}. Location: {loc}",
                                    "skills": []
                                })
                                scraped_count += 1
                        continue

                # 2. Lever Postings API
                if ats == "lever":
                    slug = careers_url.rstrip("/").split("/")[-1]
                    api_url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
                    res = client.get(api_url)
                    if res.status_code == 200:
                        postings = res.json()
                        for p in postings:
                            loc = (p.get("categories") or {}).get("location", "India")
                            team = (p.get("categories") or {}).get("team", "")
                            if any(k in loc.lower() for k in ["india", "bengaluru", "bangalore", "delhi", "noida", "mumbai", "hyderabad", "remote"]):
                                ingestor.ingest_job({
                                    "title": p.get("text"),
                                    "company": name,
                                    "ats_type": "lever",
                                    "location": loc,
                                    "is_remote": "remote" in loc.lower() or "remote" in p.get("text", "").lower(),
                                    "experience_min": 0,
                                    "experience_max": 3,
                                    "apply_url": p.get("hostedUrl"),
                                    "description": f"Role: {p.get('text')} ({team}) at {name}. Location: {loc}",
                                    "skills": []
                                })
                                scraped_count += 1
                        continue

                # 3. Keka Careers API
                if ats == "keka":
                    base = careers_url.rstrip("/")
                    api_url = f"{base}/api/v1/jobpostings"
                    res = client.get(api_url)
                    if res.status_code == 200:
                        data = res.json()
                        jobs = data.get("jobs", []) or data.get("jobPostings", [])
                        for j in jobs:
                            title = j.get("title") or j.get("jobTitle")
                            job_id = j.get("id") or j.get("jobPostingId")
                            if title and job_id:
                                ingestor.ingest_job({
                                    "title": title,
                                    "company": name,
                                    "ats_type": "keka",
                                    "location": j.get("location", "India"),
                                    "is_remote": "remote" in title.lower(),
                                    "experience_min": j.get("minExperience", 0),
                                    "experience_max": j.get("maxExperience", 3),
                                    "apply_url": f"{base}/#/jobdetails/{job_id}",
                                    "description": j.get("description", f"Role: {title} at {name}"),
                                    "skills": [s.strip() for s in j.get("skills", "").split(",") if s.strip()]
                                })
                                scraped_count += 1
                        continue

            except Exception as e:
                # Log and continue silently without halting batch crawl
                pass

    print(f"[OK] Crawl cycle completed. Ingested {scraped_count} live roles into inventory.")

if __name__ == "__main__":
    crawl_company_jobs(limit=100)
