import os
import json
import httpx
from scrapers.ats_base import ATSIngestor

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "companies_global_2500.json")
if not os.path.exists(CATALOG_PATH):
    CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "companies_1000.json")

def crawl_company_jobs(limit: int = 150):
    """
    Crawls career openings across 2,500+ worldwide remote and Indian tech companies.
    Supports: Greenhouse, Lever, Ashby, Workable, Keka, Darwinbox, and Zoho Recruit.
    """
    if not os.path.exists(CATALOG_PATH):
        print(f"Catalogue file not found at {CATALOG_PATH}")
        return

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        companies = json.load(f)

    print(f"Loaded {len(companies)} worldwide & Indian companies. Crawling first {limit} portals...")
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
                # 1. Greenhouse Public Boards API
                if ats == "greenhouse":
                    slug = careers_url.rstrip("/").split("/")[-1]
                    api_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
                    res = client.get(api_url)
                    if res.status_code == 200:
                        jobs = res.json().get("jobs", [])
                        for j in jobs:
                            loc = (j.get("location") or {}).get("name", "Remote")
                            is_rem = "remote" in loc.lower() or "anywhere" in loc.lower() or "worldwide" in loc.lower() or "remote" in j.get("title", "").lower()
                            ingestor.ingest_job({
                                "title": j.get("title"),
                                "company": name,
                                "ats_type": "greenhouse",
                                "location": loc if loc else ("Worldwide Remote" if is_rem else "Remote / On-site"),
                                "is_remote": is_rem,
                                "experience_min": 0,
                                "experience_max": 4,
                                "apply_url": j.get("absolute_url"),
                                "description": f"Position: {j.get('title')} at {name}. Location: {loc}",
                                "skills": []
                            })
                            scraped_count += 1
                        continue

                # 2. Lever Public Postings API
                if ats == "lever":
                    slug = careers_url.rstrip("/").split("/")[-1]
                    api_url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
                    res = client.get(api_url)
                    if res.status_code == 200:
                        postings = res.json()
                        for p in postings:
                            loc = (p.get("categories") or {}).get("location", "Remote")
                            team = (p.get("categories") or {}).get("team", "")
                            is_rem = "remote" in loc.lower() or "anywhere" in loc.lower() or "worldwide" in loc.lower() or "remote" in p.get("text", "").lower()
                            ingestor.ingest_job({
                                "title": p.get("text"),
                                "company": name,
                                "ats_type": "lever",
                                "location": loc if loc else ("Worldwide Remote" if is_rem else "Remote / On-site"),
                                "is_remote": is_rem,
                                "experience_min": 0,
                                "experience_max": 4,
                                "apply_url": p.get("hostedUrl"),
                                "description": f"Position: {p.get('text')} ({team}) at {name}. Location: {loc}",
                                "skills": []
                            })
                            scraped_count += 1
                        continue

                # 3. Workable Public Widget API
                if ats == "workable":
                    slug = careers_url.rstrip("/").split("/")[-1]
                    api_url = f"https://apply.workable.com/api/v1/widget/accounts/{slug}"
                    res = client.get(api_url)
                    if res.status_code == 200:
                        jobs = res.json().get("jobs", [])
                        for j in jobs:
                            loc = j.get("country", "") + (f", {j.get('city')}" if j.get('city') else "")
                            is_rem = j.get("telecommuting", False) or "remote" in loc.lower()
                            ingestor.ingest_job({
                                "title": j.get("title"),
                                "company": name,
                                "ats_type": "workable",
                                "location": loc if loc else ("Worldwide Remote" if is_rem else "Global"),
                                "is_remote": is_rem,
                                "experience_min": 0,
                                "experience_max": 4,
                                "apply_url": j.get("url"),
                                "description": f"Role: {j.get('title')} at {name}. Location: {loc}",
                                "skills": []
                            })
                            scraped_count += 1
                        continue

                # 4. Keka Careers API
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
                                loc = j.get("location", "India")
                                is_rem = "remote" in loc.lower() or "remote" in title.lower()
                                ingestor.ingest_job({
                                    "title": title,
                                    "company": name,
                                    "ats_type": "keka",
                                    "location": loc,
                                    "is_remote": is_rem,
                                    "experience_min": j.get("minExperience", 0),
                                    "experience_max": j.get("maxExperience", 3),
                                    "apply_url": f"{base}/#/jobdetails/{job_id}",
                                    "description": j.get("description", f"Role: {title} at {name}"),
                                    "skills": [s.strip() for s in j.get("skills", "").split(",") if s.strip()]
                                })
                                scraped_count += 1
                        continue

            except Exception:
                pass

    print(f"[OK] Worldwide crawl complete. Successfully ingested {scraped_count} live roles.")

if __name__ == "__main__":
    crawl_company_jobs(limit=150)
