import httpx
from bs4 import BeautifulSoup
from scrapers.ats_base import ATSIngestor

KEKA_COMPANIES = [
    # Curated list of Indian high-growth tech startups using Keka
    {"company": "Sarvam AI", "url": "https://sarvamai.keka.com/careers"},
    {"company": "Pocket FM", "url": "https://pocketfm.keka.com/careers"},
    {"company": "Jar App", "url": "https://changejar.keka.com/careers"},
    {"company": "KreditBee", "url": "https://kreditbee.keka.com/careers"},
    {"company": "Boba", "url": "https://boba.keka.com/careers"},
]

def scrape_keka_company(company_name: str, careers_url: str, ingestor: ATSIngestor):
    """Scrapes active job openings from Keka ATS portals."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }

    try:
        # Keka careers often serve JSON via api/v1/jobpostings on the same subdomain
        base_domain = careers_url.rstrip("/")
        api_url = f"{base_domain}/api/v1/jobpostings"
        
        with httpx.Client(timeout=15.0, headers=headers, follow_redirects=True) as client:
            resp = client.get(api_url)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    jobs = data.get("jobs", []) or data.get("jobPostings", [])
                    for j in jobs:
                        title = j.get("title") or j.get("jobTitle")
                        job_id = j.get("id") or j.get("jobPostingId")
                        if not title or not job_id:
                            continue
                        apply_url = f"{base_domain}/#/jobdetails/{job_id}"
                        desc = j.get("description", "") or j.get("jobDescription", "")
                        location = j.get("location", "India")
                        exp_min = j.get("minExperience", 0)
                        exp_max = j.get("maxExperience", 3)

                        ingestor.ingest_job({
                            "title": title,
                            "company": company_name,
                            "ats_type": "keka",
                            "location": location,
                            "is_remote": "remote" in location.lower() or "remote" in title.lower(),
                            "experience_min": exp_min,
                            "experience_max": exp_max,
                            "apply_url": apply_url,
                            "description": desc,
                            "skills": [s.strip() for s in j.get("skills", "").split(",") if s.strip()]
                        })
                    return
                except Exception:
                    pass

            # Fallback to HTML parsing if JSON API is protected or custom
            page_resp = client.get(careers_url)
            if page_resp.status_code == 200:
                soup = BeautifulSoup(page_resp.text, "html.parser")
                for card in soup.find_all("div", class_=lambda c: c and "job-post" in c.lower()):
                    title_elem = card.find(["h3", "h4", "a"])
                    link_elem = card.find("a", href=True)
                    if title_elem and link_elem:
                        title = title_elem.text.strip()
                        href = link_elem["href"]
                        apply_url = href if href.startswith("http") else f"{base_domain}/{href.lstrip('/')}"
                        ingestor.ingest_job({
                            "title": title,
                            "company": company_name,
                            "ats_type": "keka",
                            "location": "India",
                            "is_remote": "remote" in title.lower(),
                            "experience_min": 0,
                            "experience_max": 2,
                            "apply_url": apply_url,
                            "description": f"Role: {title} at {company_name}",
                            "skills": []
                        })
    except Exception as e:
        print(f"Error scraping Keka for {company_name}: {e}")

def run_all_keka():
    ingestor = ATSIngestor()
    for comp in KEKA_COMPANIES:
        scrape_keka_company(comp["company"], comp["url"], ingestor)

if __name__ == "__main__":
    run_all_keka()
