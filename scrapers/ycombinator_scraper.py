import httpx
import html
import json
import re
from scrapers.ats_base import ATSIngestor

YC_FEEDS = [
    "https://www.ycombinator.com/jobs/role/eng",
    "https://www.ycombinator.com/jobs/location/remote",
    "https://www.ycombinator.com/jobs/role/eng?q=fresher",
    "https://www.ycombinator.com/jobs/role/eng?q=junior",
    "https://www.ycombinator.com/jobs/role/eng?q=backend",
    "https://www.ycombinator.com/jobs/role/eng?q=frontend",
    "https://www.ycombinator.com/jobs/role/eng?q=fullstack",
    "https://www.ycombinator.com/jobs/role/eng?q=ai",
    "https://www.ycombinator.com/jobs/role/eng?q=python",
    "https://www.ycombinator.com/jobs/role/eng?q=react"
]

def scrape_ycombinator_jobs():
    """
    Scrapes official Y Combinator startup job postings.
    Extracts high-paying YC startup roles (salary, batch, remote status, direct apply link).
    """
    print("Initiating Y Combinator job scraper...")
    ingestor = ATSIngestor()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }

    seen_ids = set()
    total_ingested = 0

    with httpx.Client(timeout=15.0, headers=headers, follow_redirects=True) as client:
        for url in YC_FEEDS:
            try:
                res = client.get(url)
                if res.status_code != 200:
                    continue

                match = re.search(r'data-page="([^"]+)"', res.text)
                if not match:
                    continue

                page_data = json.loads(html.unescape(match.group(1)))
                postings = page_data.get("props", {}).get("jobPostings", [])

                for p in postings:
                    job_id = p.get("id")
                    if not job_id or job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    company_name = p.get("companyName", "YC Startup")
                    batch = p.get("companyBatchName", "")
                    title = p.get("title", "")
                    loc = p.get("location", "Remote")
                    is_rem = "remote" in loc.lower() or "remote" in title.lower()
                    salary = p.get("salaryRange", "")
                    url_suffix = p.get("url", "")
                    apply_url = f"https://www.ycombinator.com{url_suffix}" if url_suffix.startswith("/") else p.get("applyUrl", "")
                    one_liner = p.get("companyOneLiner", "")

                    desc = f"YC {batch} Startup: {company_name} - {one_liner}. Role: {title}. Compensation: {salary}. Location: {loc}."

                    ingestor.ingest_job({
                        "title": title,
                        "company": f"{company_name} (YC {batch})",
                        "ats_type": "direct",
                        "location": loc if loc else ("Worldwide Remote" if is_rem else "US / Global"),
                        "is_remote": is_rem,
                        "experience_min": 0 if "junior" in title.lower() or "intern" in title.lower() else 1,
                        "experience_max": 4,
                        "apply_url": apply_url,
                        "description": desc,
                        "skills": p.get("skills", [])
                    })
                    total_ingested += 1

            except Exception as e:
                print(f"Error scraping {url}: {e}")

    print(f"[OK] Y Combinator scrape complete. Ingested {total_ingested} official YC startup roles.")

if __name__ == "__main__":
    scrape_ycombinator_jobs()
