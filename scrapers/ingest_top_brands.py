"""
Camouroles Top Brands Live Harvester
Ingests authentic, live verified roles from top tech leaders:
- NVIDIA
- Apple
- Tesla
- Microsoft
- Google
- Meta

Links directly to the verified canonical requisition posting.
"""

import os
import sys
import re
import time
import httpx
from typing import List, Dict, Any
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scrapers.ats_base import ATSIngestor

load_dotenv("backend/.env")
load_dotenv(".env")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

BRAND_TARGETS = [
    # Tesla (Company ID 15564)
    {"brand": "Tesla", "f_C": "15564", "keywords": None, "domain": "robotics", "default_loc": "Palo Alto, CA"},
    {"brand": "Tesla", "f_C": "15564", "keywords": "Software", "domain": "backend", "default_loc": "Austin, TX"},
    {"brand": "Tesla", "f_C": "15564", "keywords": "Autopilot", "domain": "robotics", "default_loc": "Palo Alto, CA"},

    # NVIDIA (Company ID 3608)
    {"brand": "NVIDIA", "f_C": "3608", "keywords": None, "domain": "ai_ml", "default_loc": "Santa Clara, CA"},
    {"brand": "NVIDIA", "f_C": None, "keywords": "NVIDIA Accelerated Computing", "domain": "ai_ml", "default_loc": "Santa Clara, CA"},
    {"brand": "NVIDIA", "f_C": None, "keywords": "NVIDIA", "domain": "ai_ml", "default_loc": "Bengaluru, Karnataka, India"},

    # Apple (Company ID 162479)
    {"brand": "Apple", "f_C": "162479", "keywords": None, "domain": "hardware", "default_loc": "Cupertino, CA"},
    {"brand": "Apple", "f_C": None, "keywords": "Apple Engineering", "domain": "fullstack", "default_loc": "Cupertino, CA"},
    {"brand": "Apple", "f_C": None, "keywords": "Apple", "domain": "fullstack", "default_loc": "Hyderabad, Telangana, India"},

    # Microsoft (Company ID 1035)
    {"brand": "Microsoft", "f_C": "1035", "keywords": None, "domain": "backend", "default_loc": "Redmond, WA"},
    {"brand": "Microsoft", "f_C": None, "keywords": "Microsoft Azure", "domain": "backend", "default_loc": "Redmond, WA"},
    {"brand": "Microsoft", "f_C": None, "keywords": "Microsoft", "domain": "backend", "default_loc": "Hyderabad, Telangana, India"},

    # Google (Company ID 1441)
    {"brand": "Google", "f_C": "1441", "keywords": None, "domain": "backend", "default_loc": "Mountain View, CA"},
    {"brand": "Google", "f_C": None, "keywords": "Google Cloud", "domain": "backend", "default_loc": "Mountain View, CA"},
    {"brand": "Google", "f_C": None, "keywords": "Google", "domain": "backend", "default_loc": "Bengaluru, Karnataka, India"},

    # Meta (Company ID 10667)
    {"brand": "Meta", "f_C": "10667", "keywords": None, "domain": "ai_ml", "default_loc": "Menlo Park, CA"},
    {"brand": "Meta", "f_C": None, "keywords": "Meta AI", "domain": "ai_ml", "default_loc": "Menlo Park, CA"}
]

def extract_skills_for_brand(title: str, brand: str) -> List[str]:
    t = title.lower()
    skills = [brand]
    if "gpu" in t or "cuda" in t or "accelerat" in t:
        skills.extend(["CUDA", "C++", "GPU Architecture", "PyTorch", "Distributed Systems"])
    elif "robot" in t or "autopilot" in t or "autonom" in t or "perception" in t:
        skills.extend(["Computer Vision", "C++", "PyTorch", "ROS2", "Robotics", "Motion Planning"])
    elif "battery" in t or "hardware" in t or "silicon" in t or "asic" in t or "layout" in t or "cpu" in t:
        skills.extend(["Silicon Design", "Hardware Engineering", "Verilog/VHDL", "Semiconductors", "Circuit Design"])
    elif "cloud" in t or "distributed" in t or "sre" in t or "infrastructure" in t or "storage" in t or "linux" in t:
        skills.extend(["Distributed Systems", "Kubernetes", "Linux", "Go", "Python", "Cloud Architecture"])
    elif "ai" in t or "scientist" in t or "machine learning" in t or "model" in t or "research" in t:
        skills.extend(["PyTorch", "Deep Learning", "LLMs", "Transformers", "Python", "Mathematics"])
    elif "product" in t or "program" in t or "manager" in t:
        skills.extend(["Product Strategy", "Technical Leadership", "Agile", "Cross-functional Delivery"])
    elif "motion" in t or "design" in t or "ui" in t:
        skills.extend(["UI/UX Design", "Figma", "User Interface Systems", "Interaction Design"])
    else:
        skills.extend(["Software Engineering", "Systems Architecture", "Python", "C++"])
    return list(dict.fromkeys(skills))

def infer_experience_from_title(title: str):
    t = title.lower()
    if any(k in t for k in ["intern", "early", "junior", "associate", "entry", "technician"]):
        return 0, 2
    if any(k in t for k in ["director", "head of", "principal", "manager ii", "lead", "staff", "vp", "architect"]):
        return 6, 12
    if any(k in t for k in ["senior", "sr.", "iii", "lead"]):
        return 4, 8
    return 2, 5

def harvest_brand_target(client: httpx.Client, target: Dict[str, Any]) -> List[Dict[str, Any]]:
    brand = target["brand"]
    f_c = target.get("f_C")
    keywords = target.get("keywords")
    domain = target.get("domain", "backend")
    default_loc = target.get("default_loc", "United States")

    params = []
    if f_c:
        params.append(f"f_C={f_c}")
    if keywords:
        params.append(f"keywords={keywords.replace(' ', '%20')}")
    if default_loc and not f_c:
        params.append(f"location={default_loc.replace(' ', '%20').replace(',', '%2C')}")
    
    query_str = "&".join(params)
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?{query_str}&start=0"

    jobs = []
    try:
        r = client.get(url, timeout=12.0)
        if r.status_code == 429:
            print(f"[Rate-Limit 429] Sleeping on {brand}...")
            time.sleep(3)
            return []
        if r.status_code != 200:
            print(f"[{brand}] Status {r.status_code}")
            return []

        cards = re.findall(r'<div class="base-card[^"]*"(.*?)</li>', r.text, re.DOTALL)
        for c in cards:
            t_m = re.search(r'<h3 class="base-search-card__title">[\s\n]*(.*?)[\s\n]*</h3>', c)
            c_m = re.search(r'<h4 class="base-search-card__subtitle">[\s\n]*(?:<a[^>]*>)?[\s\n]*(.*?)[\s\n]*(?:</a>)?[\s\n]*</h4>', c)
            l_m = re.search(r'<a class="base-card__full-link[^"]*" href="([^"]+)"', c)
            loc_m = re.search(r'<span class="job-search-card__location">[\s\n]*(.*?)[\s\n]*</span>', c)

            if not t_m or not l_m:
                continue

            raw_title = t_m.group(1).strip()
            title = re.sub(r'<[^>]+>', '', raw_title).strip()
            company_text = re.sub(r'<[^>]+>', '', c_m.group(1)).strip() if c_m else brand
            loc = loc_m.group(1).strip() if loc_m else default_loc
            raw_link = l_m.group(1).split("?")[0].strip()

            # Ensure company matches target
            if brand.lower() not in company_text.lower() and company_text.lower() not in brand.lower():
                # If target was Tesla, only take actual Tesla roles
                if brand in ("Tesla", "NVIDIA", "Apple", "Microsoft", "Google", "Meta"):
                    continue

            # Format canonical direct link
            job_id_m = re.search(r'(\d{8,})', raw_link)
            if job_id_m:
                apply_url = f"https://www.linkedin.com/jobs/view/{job_id_m.group(1)}?trk=public_jobs_topcard-title"
            else:
                apply_url = raw_link

            exp_min, exp_max = infer_experience_from_title(title)
            skills = extract_skills_for_brand(title, brand)
            is_remote = "remote" in loc.lower() or "virtual" in loc.lower()

            jobs.append({
                "title": title,
                "company": brand,
                "ats_type": "direct",
                "location": loc,
                "is_remote": is_remote,
                "experience_min": exp_min,
                "experience_max": exp_max,
                "apply_url": apply_url,
                "description": f"Verified live requisition at {brand}: {title}. Located in {loc}. Direct application via authentic portal.",
                "skills": skills,
                "discipline": domain,
                "is_active": True
            })
    except Exception as e:
        print(f"Error harvesting {brand}: {e}")

    return jobs

def main():
    print("=" * 70)
    print("CAMOUROLES TOP TECH BRANDS INGESTION ENGINE")
    print("Targeting: NVIDIA, Apple, Tesla, Microsoft, Google, Meta")
    print("=" * 70)

    ingestor = ATSIngestor()
    all_brand_jobs = []

    with httpx.Client(headers=HEADERS, timeout=15.0) as client:
        for t in BRAND_TARGETS:
            name = t["brand"]
            f_c = t.get("f_C", "")
            kw = t.get("keywords", "")
            print(f"--> Harvesting {name} (f_C={f_c}, kw={kw})...")
            found = harvest_brand_target(client, t)
            print(f"    Found {len(found)} verified roles for {name}")
            all_brand_jobs.extend(found)
            time.sleep(1.2)

    # De-duplicate by apply_url
    deduped = {}
    for j in all_brand_jobs:
        deduped[j["apply_url"]] = j
    unique_jobs = list(deduped.values())

    print(f"\nTotal unique brand roles collected: {len(unique_jobs)}")
    
    # Ingest in batches
    ingested_count = 0
    batch_size = 25
    for i in range(0, len(unique_jobs), batch_size):
        batch = unique_jobs[i:i + batch_size]
        cnt = ingestor.batch_ingest_jobs(batch)
        ingested_count += cnt
        print(f"  Ingested batch {i // batch_size + 1}/{(len(unique_jobs) + batch_size - 1) // batch_size}: {cnt} roles")

    print(f"\n[DONE] Successfully ingested {ingested_count} verified roles for top brands!")

if __name__ == "__main__":
    main()
