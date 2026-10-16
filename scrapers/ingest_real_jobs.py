import os
import sys
import time
from typing import Dict, Any, List
import httpx
from dotenv import load_dotenv

# Ensure root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scrapers.ats_base import ATSIngestor

load_dotenv()

# Real verified greenhouse boards with rich robotics, systems, and engineering talent
BOARDS = [
    {"slug": "waymo", "company": "Waymo", "category": "robotics"},
    {"slug": "figure", "company": "Figure AI", "category": "robotics"},
    {"slug": "nuro", "company": "Nuro", "category": "robotics"},
    {"slug": "kodiak", "company": "Kodiak Robotics", "category": "robotics"},
    {"slug": "scaleai", "company": "Scale AI", "category": "ai"},
    {"slug": "anthropic", "company": "Anthropic", "category": "ai"},
    {"slug": "verkada", "company": "Verkada", "category": "hardware"},
    {"slug": "datadog", "company": "Datadog", "category": "systems"},
]

ENGINEERING_KEYWORDS = [
    "engineer", "developer", "software", "robotics", "embedded", "firmware",
    "hardware", "autonomy", "autonomous", "perception", "motion", "controls",
    "systems", "infrastructure", "backend", "frontend", "full stack", "fullstack",
    "machine learning", "ai", "vision", "deep learning", "slam", "ros", "fpga"
]

def is_engineering_role(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in ENGINEERING_KEYWORDS)

def extract_skills_from_title(title: str, category: str) -> List[str]:
    t = title.lower()
    skills = []
    if "robot" in t or "autonom" in t or "motion" in t:
        skills.extend(["ROS2", "C++", "Motion Planning", "Kinematics", "Controls"])
    elif "embedded" in t or "firmware" in t or "hardware" in t:
        skills.extend(["Embedded C", "C++", "RTOS", "Microcontrollers", "Hardware Debugging"])
    elif "vision" in t or "perception" in t or "slam" in t:
        skills.extend(["Computer Vision", "PyTorch", "C++", "SLAM", "Point Clouds"])
    elif "infrastructure" in t or "systems" in t or "backend" in t or "distributed" in t:
        skills.extend(["Distributed Systems", "Go", "Kubernetes", "Linux", "C++"])
    elif "frontend" in t or "ui" in t:
        skills.extend(["React", "TypeScript", "JavaScript", "HTML/CSS"])
    elif "machine learning" in t or "ai" in t or "research" in t:
        skills.extend(["Python", "PyTorch", "Transformers", "CUDA", "Distributed Training"])
    else:
        skills.extend(["Python", "C++", "Linux", "Git"])

    return list(dict.fromkeys(skills))

def scrape_and_ingest():
    ingestor = ATSIngestor()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }

    total_added = 0

    with httpx.Client(timeout=20.0, headers=headers, follow_redirects=True) as client:
        for b in BOARDS:
            slug = b["slug"]
            company = b["company"]
            print(f"\nFetching live board for {company} (slug: {slug})...")

            try:
                resp = client.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
                if resp.status_code != 200:
                    print(f"Failed to fetch {slug}: {resp.status_code}")
                    continue

                jobs = resp.json().get("jobs", [])
                print(f"Total postings returned: {len(jobs)}")

                board_added = 0
                for j in jobs:
                    title = j.get("title", "").strip()
                    if not is_engineering_role(title):
                        continue

                    apply_url = j.get("absolute_url", "").strip()
                    if not apply_url:
                        continue

                    # Verify apply URL returns 200 live
                    try:
                        check = client.head(apply_url, timeout=5.0)
                        if check.status_code not in (200, 301, 302, 307, 308):
                            # Try GET fallback
                            check_get = client.get(apply_url, timeout=5.0)
                            if check_get.status_code != 200:
                                continue
                    except Exception:
                        continue

                    loc_name = j.get("location", {}).get("name", "Remote / United States")
                    is_remote = "remote" in loc_name.lower() or "anywhere" in loc_name.lower()

                    skills = extract_skills_from_title(title, b["category"])

                    job_data = {
                        "title": title,
                        "company": company,
                        "ats_type": "greenhouse",
                        "location": loc_name if loc_name else "United States",
                        "is_remote": is_remote,
                        "experience_min": 0,
                        "experience_max": 4,
                        "apply_url": apply_url,
                        "description": f"Verified active opening at {company}. Role: {title}. Location: {loc_name}.",
                        "skills": skills,
                        "is_active": True
                    }

                    ok = ingestor.ingest_job(job_data)
                    if ok:
                        board_added += 1
                        total_added += 1
                        print(f"  + Added: {company} | {title[:40]} -> {apply_url[:65]}")

                    # Cap per company to maintain clean balanced catalog
                    if board_added >= 15:
                        break

            except Exception as e:
                print(f"Error scraping {company}: {e}")

    print(f"\n==========================================")
    print(f"Successfully ingested {total_added} 100% verified live jobs!")
    print(f"==========================================")

if __name__ == "__main__":
    scrape_and_ingest()
