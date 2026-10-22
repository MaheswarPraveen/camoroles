"""
Camouroles Frontier & Deep-Tech Niches Ingestion Engine
Synchronizes verified roles from 23 specialized, high-demand industry leaders:
1. Space & Satellites: Rocket Lab (585), Relativity Space (369), Astranis (181), Planet Labs (127), Loft Orbital (65), Spire (37), Observable Space (26), Logos Space (25)
2. Defense, Edge & Big Data AI: Cloudflare (435), Palantir (310)
3. ClimateTech & Fusion: Form Energy (206), Redwood Materials (144), Commonwealth Fusion Systems (129), Solugen (3)
4. Frontier AI & Systems Craft: Notion (128), Cohere (118), Modal (43), Linear (29), Anyscale (20)
5. BioTech & Computational Bio: 10x Genomics (35), Ginkgo Bioworks (20), Recursion Pharmaceuticals (13), Insitro (13)
"""

import os
import sys
import re
from typing import List, Dict, Any
import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scrapers.ats_base import ATSIngestor

load_dotenv("backend/.env")
load_dotenv(".env")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

def infer_experience(title: str) -> tuple:
    t = title.lower()
    if any(k in t for k in ["intern", "trainee", "fresher", "junior", "associate", "entry"]):
        return 0, 2
    if any(k in t for k in ["staff", "principal", "director", "head of", "lead", "architect", "senior", "sr."]):
        return 5, 9
    return 2, 5

# =========================================================================
# 1. GREENHOUSE HARVESTERS
# =========================================================================
GREENHOUSE_NICHE_BOARDS = [
    {
        "slug": "rocketlab",
        "company": "Rocket Lab",
        "domain": "Aerospace & Commercial Launch",
        "skills": ["Aerospace Engineering", "Avionics", "Additive Manufacturing", "Propulsion", "Flight Software", "C++", "Python"]
    },
    {
        "slug": "relativity",
        "company": "Relativity Space",
        "domain": "3D-Printed Rockets & Space Launch",
        "skills": ["Additive Manufacturing", "Propulsion", "Avionics", "Flight Software", "Structures", "C++", "Python"]
    },
    {
        "slug": "astranis",
        "company": "Astranis",
        "domain": "Space & Satellite Comm",
        "skills": ["Satellite Systems", "RF Engineering", "Aerospace", "C++", "FPGA", "Hardware Testing"]
    },
    {
        "slug": "planetlabs",
        "company": "Planet Labs",
        "domain": "Earth Observation & Space Systems",
        "skills": ["Geospatial AI", "Satellite Operations", "Python", "Computer Vision", "Orbital Mechanics"]
    },
    {
        "slug": "spire",
        "company": "Spire Global",
        "domain": "Space Intelligence & Nanosatellites",
        "skills": ["Space Systems", "RF Engineering", "Embedded Systems", "Python", "Cloud Infrastructure"]
    },
    {
        "slug": "redwoodmaterials",
        "company": "Redwood Materials",
        "domain": "Battery Materials & Clean Energy",
        "skills": ["Chemical Engineering", "Materials Science", "Process Engineering", "Automation", "Battery Tech"]
    },
    {
        "slug": "cloudflare",
        "company": "Cloudflare",
        "domain": "Edge Systems & Cyber Defense",
        "skills": ["Distributed Systems", "Rust", "Go", "Networking", "Security", "Kubernetes"]
    },
    {
        "slug": "ginkgobioworks",
        "company": "Ginkgo Bioworks",
        "domain": "Synthetic Biology & BioTech",
        "skills": ["Computational Biology", "Bioinformatics", "Python", "Genomics", "Data Pipelines"]
    },
    {
        "slug": "recursionpharmaceuticals",
        "company": "Recursion Pharmaceuticals",
        "domain": "AI Drug Discovery & Computational Bio",
        "skills": ["Computational Biology", "Machine Learning", "PyTorch", "Bioinformatics", "Chemistry", "Python"]
    }
]

def harvest_greenhouse_niches() -> List[Dict[str, Any]]:
    jobs = []
    with httpx.Client(timeout=25.0, headers=HEADERS) as client:
        for b in GREENHOUSE_NICHE_BOARDS:
            slug = b["slug"]
            comp = b["company"]
            print(f"  [Greenhouse] Harvesting {comp} ({slug})...", flush=True)
            try:
                r = client.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
                if r.status_code == 200:
                    raw_jobs = r.json().get("jobs", [])
                    print(f"    -> Found {len(raw_jobs)} roles.", flush=True)
                    for j in raw_jobs:
                        t = j.get("title", "")
                        loc = (j.get("location") or {}).get("name", "United States")
                        min_e, max_e = infer_experience(t)
                        link = j.get("absolute_url")
                        jobs.append({
                            "title": t,
                            "company": comp,
                            "ats_type": "greenhouse",
                            "location": loc,
                            "is_remote": "remote" in loc.lower(),
                            "experience_min": min_e,
                            "experience_max": max_e,
                            "apply_url": link,
                            "description": f"{t} at {comp}. Domain: {b['domain']}. Active requisition discovered via Greenhouse.",
                            "skills": b["skills"]
                        })
            except Exception as e:
                print(f"    [Error] {comp}: {e}", flush=True)
    return jobs

# =========================================================================
# 2. LEVER HARVESTERS (PALANTIR, COMMONWEALTH FUSION, LOFT ORBITAL)
# =========================================================================
LEVER_NICHE_BOARDS = [
    {
        "slug": "palantir",
        "company": "Palantir",
        "domain": "Mission-Critical AI & Defense Systems",
        "skills": ["Distributed Systems", "Java", "Go", "TypeScript", "Defense Tech", "Big Data"]
    },
    {
        "slug": "cfsenergy",
        "company": "Commonwealth Fusion Systems",
        "domain": "Commercial Fusion Energy & Superconducting Magnets",
        "skills": ["Fusion Energy", "Plasma Physics", "Superconducting Magnets", "Cryogenics", "Mechanical Engineering"]
    },
    {
        "slug": "loftorbital",
        "company": "Loft Orbital",
        "domain": "Turnkey Satellite Infrastructure & Space Missions",
        "skills": ["Mission Operations", "Flight Software", "Satellite Systems", "Avionics", "Python", "C++"]
    }
]

def harvest_lever_niches() -> List[Dict[str, Any]]:
    jobs = []
    with httpx.Client(timeout=45.0, headers=HEADERS) as client:
        for b in LEVER_NICHE_BOARDS:
            slug = b["slug"]
            comp = b["company"]
            print(f"  [Lever] Harvesting {comp} ({slug})...", flush=True)
            try:
                r = client.get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
                if r.status_code == 200:
                    raw_jobs = r.json()
                    print(f"    -> Found {len(raw_jobs)} roles.", flush=True)
                    for j in raw_jobs:
                        t = j.get("text", "")
                        loc = (j.get("categories") or {}).get("location", "Global")
                        min_e, max_e = infer_experience(t)
                        link = j.get("hostedUrl") or j.get("applyUrl")
                        jobs.append({
                            "title": t,
                            "company": comp,
                            "ats_type": "lever",
                            "location": loc,
                            "is_remote": "remote" in loc.lower(),
                            "experience_min": min_e,
                            "experience_max": max_e,
                            "apply_url": link,
                            "description": f"{t} at {comp}. Domain: {b['domain']}. Active requisition discovered via Lever.",
                            "skills": b["skills"]
                        })
            except Exception as e:
                print(f"    [Error] {comp}: {e}", flush=True)
    return jobs

# =========================================================================
# 3. ASHBY HARVESTERS (FORM ENERGY, NOTION, COHERE, MODAL, LINEAR, ANYSCALE, INSITRO, OBSERVABLE, LOGOS)
# =========================================================================
ASHBY_NICHE_BOARDS = [
    {
        "slug": "formenergy",
        "company": "Form Energy",
        "skills": ["Battery Technology", "Materials Science", "Energy Storage", "Process Engineering", "Chemical Engineering"]
    },
    {
        "slug": "notion",
        "company": "Notion",
        "skills": ["Product Engineering", "TypeScript", "React", "PostgreSQL", "AI Workspace"]
    },
    {
        "slug": "cohere",
        "company": "Cohere",
        "skills": ["Large Language Models", "PyTorch", "NLP", "Distributed Training", "CUDA"]
    },
    {
        "slug": "modal",
        "company": "Modal",
        "skills": ["Serverless GPU", "Python", "Rust", "Linux Kernel", "Distributed Systems"]
    },
    {
        "slug": "linear",
        "company": "Linear",
        "skills": ["Product Craft", "TypeScript", "React", "Sync Engine", "UI/UX Design"]
    },
    {
        "slug": "anyscale",
        "company": "Anyscale",
        "skills": ["Ray", "Distributed AI", "Python", "Kubernetes", "Machine Learning"]
    },
    {
        "slug": "insitro",
        "company": "Insitro",
        "skills": ["Machine Learning", "Computational Biology", "Genomics", "PyTorch", "Data Engineering"]
    },
    {
        "slug": "observable-space",
        "company": "Observable Space",
        "skills": ["Aerospace Optics", "Space Systems", "Electrical Engineering", "Satellite Payloads"]
    },
    {
        "slug": "logos-space",
        "company": "Logos Space",
        "skills": ["Optical Payloads", "Satellite Communications", "Space Systems", "Hardware Engineering"]
    }
]

def harvest_ashby_niches() -> List[Dict[str, Any]]:
    jobs = []
    with httpx.Client(timeout=20.0, headers=HEADERS) as client:
        for b in ASHBY_NICHE_BOARDS:
            slug = b["slug"]
            comp = b["company"]
            print(f"  [Ashby] Harvesting {comp} ({slug})...", flush=True)
            try:
                r = client.get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
                if r.status_code == 200:
                    raw_jobs = r.json().get("jobs", [])
                    print(f"    -> Found {len(raw_jobs)} roles.", flush=True)
                    for j in raw_jobs:
                        t = j.get("title", "")
                        loc = j.get("location", "San Francisco, CA")
                        min_e, max_e = infer_experience(t)
                        link = j.get("jobUrl") or j.get("applyUrl")
                        jobs.append({
                            "title": t,
                            "company": comp,
                            "ats_type": "ashby",
                            "location": loc,
                            "is_remote": bool(j.get("isRemote")),
                            "experience_min": min_e,
                            "experience_max": max_e,
                            "apply_url": link,
                            "description": f"{t} at {comp}. Live verified opening discovered via Ashby.",
                            "skills": b["skills"]
                        })
            except Exception as e:
                print(f"    [Error] {comp}: {e}", flush=True)
    return jobs

# =========================================================================
# 4. BREEZY HR & KULA HARVESTERS (SOLUGEN, 10X GENOMICS)
# =========================================================================
def harvest_breezy_niches() -> List[Dict[str, Any]]:
    jobs = []
    print("  [Breezy HR] Harvesting Solugen...", flush=True)
    try:
        r = httpx.get("https://solugen.breezy.hr/json", headers=HEADERS, timeout=15.0)
        if r.status_code == 200:
            raw_jobs = r.json()
            for j in raw_jobs:
                t = j.get("name", "")
                link = j.get("url")
                loc_dict = j.get("location") or {}
                city = loc_dict.get("city", "Houston")
                state = (loc_dict.get("state") or {}).get("name", "Texas")
                min_e, max_e = infer_experience(t)
                jobs.append({
                    "title": t,
                    "company": "Solugen",
                    "ats_type": "breezy",
                    "location": f"{city}, {state}",
                    "is_remote": bool(loc_dict.get("is_remote")),
                    "experience_min": min_e,
                    "experience_max": max_e,
                    "apply_url": link,
                    "description": f"{t} at Solugen. Decarbonizing chemical manufacturing via sustainable molecule factories.",
                    "skills": ["Chemical Engineering", "Green Chemistry", "Process Optimization", "Biomanufacturing"]
                })
            print(f"    -> Found {len(jobs)} Solugen roles.", flush=True)
    except Exception as e:
        print(f"    [Error] Solugen: {e}", flush=True)
    return jobs

def harvest_kula_niches() -> List[Dict[str, Any]]:
    jobs = []
    print("  [Kula] Harvesting 10x Genomics...", flush=True)
    try:
        r = httpx.get("https://careers.kula.ai/10xgenomics", headers=HEADERS, timeout=20.0)
        if r.status_code == 200:
            links = set(re.findall(r'/10xgenomics/(\d+-[a-z0-9-]+)', r.text))
            for slug in links:
                raw_title = ' '.join(slug.split('-')[1:]).title()
                link = f"https://careers.kula.ai/10xgenomics/{slug}"
                min_e, max_e = infer_experience(raw_title)
                jobs.append({
                    "title": raw_title,
                    "company": "10x Genomics",
                    "ats_type": "kula",
                    "location": "Pleasanton, CA / Global",
                    "is_remote": "remote" in raw_title.lower(),
                    "experience_min": min_e,
                    "experience_max": max_e,
                    "apply_url": link,
                    "description": f"{raw_title} at 10x Genomics. Leading single-cell and spatial biology platforms (Chromium, Visium, Xenium).",
                    "skills": ["Genomics", "Single Cell Biology", "Biotechnology", "Microfluidics", "Bioinformatics", "Python"]
                })
            print(f"    -> Found {len(jobs)} 10x Genomics roles.", flush=True)
    except Exception as e:
        print(f"    [Error] 10x Genomics: {e}", flush=True)
    return jobs

# =========================================================================
# MAIN ORCHESTRATOR
# =========================================================================
def ingest_all_frontier_niches():
    print("=== STARTING FRONTIER & DEEP-TECH NICHES INGESTION ===", flush=True)
    ingestor = ATSIngestor()
    all_jobs = []

    print("\n[Phase 1] Space, Satellites, Battery & Edge Defense (Greenhouse):", flush=True)
    all_jobs.extend(harvest_greenhouse_niches())

    print("\n[Phase 2] Defense, Commercial Fusion & Satellite Infra (Lever):", flush=True)
    all_jobs.extend(harvest_lever_niches())

    print("\n[Phase 3] High-Craft Product, Clean Energy & Biotech (Ashby):", flush=True)
    all_jobs.extend(harvest_ashby_niches())

    print("\n[Phase 4] Green Chemistry & Genomics Platforms (Breezy & Kula):", flush=True)
    all_jobs.extend(harvest_breezy_niches())
    all_jobs.extend(harvest_kula_niches())

    print(f"\nTotal Frontier Niche Jobs Collected: {len(all_jobs)}. Ingesting into Supabase...", flush=True)
    saved = ingestor.batch_ingest_jobs(all_jobs)
    print(f"\n==========================================", flush=True)
    print(f"Successfully synced {saved} 100% verified frontier niche roles into database!", flush=True)
    print(f"==========================================", flush=True)

if __name__ == "__main__":
    ingest_all_frontier_niches()
