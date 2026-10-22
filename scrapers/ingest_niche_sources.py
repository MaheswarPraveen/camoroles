"""
Camouroles Niche Sources Ingestion Engine
Fetches real, verified jobs from high-signal, niche platforms discovered via research:
1. Frontier AI & Robotics: Figure AI, Skydio, Shield AI, Zoox
2. Gaming Studios & Indie Game Dev: Riot Games, Bungie, Work With Indies
3. High-Quality Remote Tech: Remotive API
4. Regional Tech & Design: Hasjob (India / Bengaluru)
"""

import os
import sys
import re
import html
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scrapers.ingest_real_jobs import ATSIngestor

load_dotenv("backend/.env")
load_dotenv(".env")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json, text/xml, application/xml, text/html, */*"
}

def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', raw_html)
    clean = html.unescape(clean)
    return re.sub(r'\s+', ' ', clean).strip()

def infer_experience(title: str) -> tuple:
    t = title.lower()
    if any(k in t for k in ["intern", "trainee", "fresher", "junior", "associate", "entry"]):
        return 0, 2
    if any(k in t for k in ["staff", "principal", "director", "head of", "lead", "architect", "senior", "sr."]):
        return 5, 9
    return 2, 5

# =========================================================================
# 1. FRONTIER AI & ROBOTICS ATS ENDPOINTS
# =========================================================================
def fetch_figure_ai() -> List[Dict[str, Any]]:
    """Figure AI (Greenhouse)"""
    url = "https://boards-api.greenhouse.io/v1/boards/figure/jobs"
    jobs = []
    try:
        r = httpx.get(url, headers=HEADERS, timeout=12.0)
        if r.status_code == 200:
            for j in r.json().get("jobs", []):
                t = j.get("title", "")
                loc = (j.get("location") or {}).get("name", "Sunnyvale, CA")
                min_e, max_e = infer_experience(t)
                jobs.append({
                    "title": t,
                    "company": "Figure AI",
                    "ats_type": "greenhouse",
                    "location": loc,
                    "is_remote": "remote" in loc.lower(),
                    "experience_min": min_e,
                    "experience_max": max_e,
                    "apply_url": j.get("absolute_url"),
                    "description": f"{t} at Figure AI (Humanoid Robotics). Work on AI, whole-body control, actuators, and embodied autonomy.",
                    "skills": ["Robotics", "C++", "Python", "Computer Vision", "Control Systems", "AI Hardware"]
                })
    except Exception as e:
        print(f"[Figure AI Error]: {e}")
    return jobs

def fetch_skydio() -> List[Dict[str, Any]]:
    """Skydio (Ashby)"""
    url = "https://api.ashbyhq.com/posting-api/job-board/skydio"
    jobs = []
    try:
        r = httpx.get(url, headers=HEADERS, timeout=12.0)
        if r.status_code == 200:
            for j in r.json().get("jobs", []):
                t = j.get("title", "")
                loc = j.get("location", "San Mateo, CA")
                min_e, max_e = infer_experience(t)
                link = j.get("jobUrl") or j.get("applyUrl")
                jobs.append({
                    "title": t,
                    "company": "Skydio",
                    "ats_type": "ashby",
                    "location": loc,
                    "is_remote": bool(j.get("isRemote")),
                    "experience_min": min_e,
                    "experience_max": max_e,
                    "apply_url": link,
                    "description": f"{t} at Skydio. Autonomous drones, real-time computer vision, edge AI, and flight systems.",
                    "skills": ["Autonomous Flight", "Embedded C++", "Python", "ROS2", "Computer Vision", "Perception"]
                })
    except Exception as e:
        print(f"[Skydio Error]: {e}")
    return jobs

def fetch_shield_ai() -> List[Dict[str, Any]]:
    """Shield AI (Lever)"""
    url = "https://api.lever.co/v0/postings/shieldai?mode=json"
    jobs = []
    try:
        r = httpx.get(url, headers=HEADERS, timeout=12.0)
        if r.status_code == 200:
            for j in r.json():
                t = j.get("text", "")
                loc = (j.get("categories") or {}).get("location", "San Diego, CA")
                min_e, max_e = infer_experience(t)
                link = j.get("hostedUrl") or j.get("applyUrl")
                jobs.append({
                    "title": t,
                    "company": "Shield AI",
                    "ats_type": "lever",
                    "location": loc,
                    "is_remote": "remote" in loc.lower(),
                    "experience_min": min_e,
                    "experience_max": max_e,
                    "apply_url": link,
                    "description": f"{t} at Shield AI (Hivemind AI Pilot). Developing state-of-the-art autonomy algorithms and defense software.",
                    "skills": ["Autonomy", "C++", "State Estimation", "Reinforcement Learning", "Linux", "ROS"]
                })
    except Exception as e:
        print(f"[Shield AI Error]: {e}")
    return jobs

def fetch_zoox() -> List[Dict[str, Any]]:
    """Zoox (Lever)"""
    url = "https://api.lever.co/v0/postings/zoox?mode=json"
    jobs = []
    try:
        r = httpx.get(url, headers=HEADERS, timeout=12.0)
        if r.status_code == 200:
            for j in r.json():
                t = j.get("text", "")
                loc = (j.get("categories") or {}).get("location", "Foster City, CA")
                min_e, max_e = infer_experience(t)
                link = j.get("hostedUrl") or j.get("applyUrl")
                jobs.append({
                    "title": t,
                    "company": "Zoox",
                    "ats_type": "lever",
                    "location": loc,
                    "is_remote": "remote" in loc.lower(),
                    "experience_min": min_e,
                    "experience_max": max_e,
                    "apply_url": link,
                    "description": f"{t} at Zoox (Autonomous Robotaxi). Building custom autonomous mobility hardware, software, and fleet systems.",
                    "skills": ["Autonomous Driving", "C++", "Python", "Robotics", "Perception", "Sensor Fusion"]
                })
    except Exception as e:
        print(f"[Zoox Error]: {e}")
    return jobs

# =========================================================================
# 2. GAMING STUDIOS & INDIE GAME DEV
# =========================================================================
def fetch_riot_games() -> List[Dict[str, Any]]:
    """Riot Games (Greenhouse)"""
    url = "https://boards-api.greenhouse.io/v1/boards/riotgames/jobs"
    jobs = []
    try:
        r = httpx.get(url, headers=HEADERS, timeout=15.0)
        if r.status_code == 200:
            for j in r.json().get("jobs", []):
                t = j.get("title", "")
                loc = (j.get("location") or {}).get("name", "Los Angeles, CA")
                min_e, max_e = infer_experience(t)
                link = j.get("absolute_url")
                jobs.append({
                    "title": t,
                    "company": "Riot Games",
                    "ats_type": "greenhouse",
                    "location": loc,
                    "is_remote": "remote" in loc.lower(),
                    "experience_min": min_e,
                    "experience_max": max_e,
                    "apply_url": link,
                    "description": f"{t} at Riot Games. Creators of League of Legends, Valorant, and Teamfight Tactics.",
                    "skills": ["C++", "Unreal Engine", "Game Design", "3D Art", "Gameplay Engineering", "Animation"]
                })
    except Exception as e:
        print(f"[Riot Games Error]: {e}")
    return jobs

def fetch_bungie() -> List[Dict[str, Any]]:
    """Bungie (Greenhouse)"""
    url = "https://boards-api.greenhouse.io/v1/boards/bungie/jobs"
    jobs = []
    try:
        r = httpx.get(url, headers=HEADERS, timeout=12.0)
        if r.status_code == 200:
            for j in r.json().get("jobs", []):
                t = j.get("title", "")
                loc = (j.get("location") or {}).get("name", "Bellevue, WA")
                min_e, max_e = infer_experience(t)
                link = j.get("absolute_url")
                jobs.append({
                    "title": t,
                    "company": "Bungie",
                    "ats_type": "greenhouse",
                    "location": loc,
                    "is_remote": "remote" in loc.lower(),
                    "experience_min": min_e,
                    "experience_max": max_e,
                    "apply_url": link,
                    "description": f"{t} at Bungie. Creators of Destiny 2 and Marathon. AAA game production and gameplay systems.",
                    "skills": ["C++", "Unreal Engine", "Game Mechanics", "Gameplay Engineering", "3D VFX"]
                })
    except Exception as e:
        print(f"[Bungie Error]: {e}")
    return jobs

def fetch_work_with_indies() -> List[Dict[str, Any]]:
    """Work With Indies (RSS Feed)"""
    url = "https://www.workwithindies.com/careers/rss.xml"
    jobs = []
    try:
        r = httpx.get(url, headers=HEADERS, timeout=12.0)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:25]:
                raw_title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                desc = item.find("description").text if item.find("description") is not None else ""
                
                # Parse title e.g. "Scape is hiring a Senior Producer to work from Anywhere"
                comp = "Indie Studio"
                title = raw_title
                m = re.search(r'^(.*?)\s+is hiring (?:a|an)\s+(.*?)(?:\s+to work|\s+in|\s*$)', raw_title, re.I)
                if m:
                    comp = m.group(1).strip()
                    title = m.group(2).strip()

                min_e, max_e = infer_experience(title)
                jobs.append({
                    "title": title,
                    "company": comp,
                    "ats_type": "direct",
                    "location": "Worldwide Remote",
                    "is_remote": True,
                    "experience_min": min_e,
                    "experience_max": max_e,
                    "apply_url": link,
                    "description": f"{title} at {comp}. Live verified opening discovered via Work With Indies.",
                    "skills": ["Game Design", "Unity", "Unreal Engine", "C#", "C++", "Indie Games", "3D Art"]
                })
    except Exception as e:
        print(f"[Work With Indies Error]: {e}")
    return jobs

# =========================================================================
# 3. HIGH SIGNAL REMOTE TECH (REMOTIVE API)
# =========================================================================
def fetch_remotive() -> List[Dict[str, Any]]:
    """Remotive Public API"""
    url = "https://remotive.com/api/remote-jobs?limit=50"
    jobs = []
    try:
        r = httpx.get(url, headers=HEADERS, timeout=15.0)
        if r.status_code == 200:
            for j in r.json().get("jobs", []):
                t = j.get("title", "")
                comp = j.get("company_name", "Remote Tech")
                loc = j.get("candidate_required_location") or "Worldwide Remote"
                link = j.get("url")
                min_e, max_e = infer_experience(t)
                tags = j.get("tags", [])
                skills = tags[:5] if tags else ["Software Engineering", "Python", "Cloud", "API"]
                jobs.append({
                    "title": t,
                    "company": comp,
                    "ats_type": "direct",
                    "location": loc,
                    "is_remote": True,
                    "experience_min": min_e,
                    "experience_max": max_e,
                    "apply_url": link,
                    "description": f"{t} at {comp}. Live verified opening discovered via Remotive. {clean_html(j.get('description', ''))[:200]}...",
                    "skills": skills
                })
    except Exception as e:
        print(f"[Remotive Error]: {e}")
    return jobs

# =========================================================================
# 4. REGIONAL TECH & DESIGN (HASJOB INDIA)
# =========================================================================
def fetch_hasjob() -> List[Dict[str, Any]]:
    """Hasjob India (Atom XML)"""
    url = "https://hasjob.co/feed"
    jobs = []
    try:
        r = httpx.get(url, headers=HEADERS, timeout=12.0)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns):
                raw_title = entry.find("atom:title", ns).text if entry.find("atom:title", ns) is not None else ""
                link_el = entry.find("atom:link", ns)
                link = link_el.attrib.get("href") if link_el is not None else ""
                
                # Title format: "Product Designer at Chaos Engine Labs - AI-native casual mobile games, Bengaluru"
                title = raw_title
                comp = "Startup"
                loc = "Bengaluru, India"
                if " at " in raw_title:
                    parts = raw_title.split(" at ", 1)
                    title = parts[0].strip()
                    comp_loc = parts[1].split(",", 1)
                    comp = comp_loc[0].split(" - ")[0].strip()
                    if len(comp_loc) > 1:
                        loc = f"{comp_loc[1].strip()}, India"

                min_e, max_e = infer_experience(title)
                jobs.append({
                    "title": title,
                    "company": comp,
                    "ats_type": "direct",
                    "location": loc,
                    "is_remote": "remote" in raw_title.lower(),
                    "experience_min": min_e,
                    "experience_max": max_e,
                    "apply_url": link,
                    "description": f"{title} at {comp}. Live verified tech opening discovered via Hasjob India.",
                    "skills": ["Software Engineering", "Product Design", "Python", "UI/UX", "JavaScript"]
                })
    except Exception as e:
        print(f"[Hasjob Error]: {e}")
    return jobs

# =========================================================================
# 5. EUROPE / DACH OPEN TECH (ARBEITNOW API)
# =========================================================================
def fetch_arbeitnow() -> List[Dict[str, Any]]:
    """Arbeitnow Public API (Germany, Switzerland, Austria, UK, EU)"""
    url = "https://www.arbeitnow.com/api/job-board-api?page=1"
    jobs = []
    try:
        r = httpx.get(url, headers=HEADERS, timeout=15.0)
        if r.status_code == 200:
            for j in r.json().get("data", [])[:100]:
                t = j.get("title", "")
                comp = j.get("company_name", "European Employer")
                loc = j.get("location", "Berlin, Germany")
                link = j.get("url")
                min_e, max_e = infer_experience(t)
                tags = j.get("tags", [])
                skills = tags[:5] if tags else ["Software Engineering", "Python", "Cloud", "API"]
                jobs.append({
                    "title": t,
                    "company": comp,
                    "ats_type": "direct",
                    "location": loc,
                    "is_remote": bool(j.get("remote")),
                    "experience_min": min_e,
                    "experience_max": max_e,
                    "apply_url": link,
                    "description": f"{t} at {comp} ({loc}). Live verified opening discovered via Arbeitnow Europe.",
                    "skills": skills
                })
    except Exception as e:
        print(f"[Arbeitnow Error]: {e}")
    return jobs

# =========================================================================
# 6. EMEA & MIDDLE EAST REMOTE (JOBICY API)
# =========================================================================
def fetch_jobicy_emea() -> List[Dict[str, Any]]:
    """Jobicy Public API (EMEA & Middle East)"""
    url = "https://jobicy.com/api/v2/remote-jobs?geo=emea&count=50"
    jobs = []
    try:
        r = httpx.get(url, headers=HEADERS, timeout=15.0)
        if r.status_code == 200:
            for j in r.json().get("jobs", []):
                t = j.get("jobTitle", "")
                comp = j.get("companyName", "Tech Employer")
                loc = f"{j.get('jobGeo', 'EMEA')} (Remote)"
                link = j.get("url")
                min_e, max_e = infer_experience(t)
                tags = j.get("jobIndustry", [])
                skills = tags[:5] if tags else ["Engineering", "Cloud", "Product"]
                jobs.append({
                    "title": t,
                    "company": comp,
                    "ats_type": "direct",
                    "location": loc,
                    "is_remote": True,
                    "experience_min": min_e,
                    "experience_max": max_e,
                    "apply_url": link,
                    "description": f"{t} at {comp}. Live verified opening discovered via Jobicy EMEA.",
                    "skills": skills
                })
    except Exception as e:
        print(f"[Jobicy EMEA Error]: {e}")
    return jobs

def ingest_all_niche_jobs():
    print("=== STARTING NICHE & UNDERGROUND SOURCES INGESTION ===", flush=True)
    ingestor = ATSIngestor()
    all_jobs = []

    print("1. Fetching Figure AI (Humanoid Robotics)...", flush=True)
    fig_jobs = fetch_figure_ai()
    print(f"   -> {len(fig_jobs)} roles found.")
    all_jobs.extend(fig_jobs)

    print("2. Fetching Skydio (Autonomous Flight / AI)...", flush=True)
    sky_jobs = fetch_skydio()
    print(f"   -> {len(sky_jobs)} roles found.")
    all_jobs.extend(sky_jobs)

    print("3. Fetching Shield AI (Autonomous Defense / Aircraft)...", flush=True)
    sh_jobs = fetch_shield_ai()
    print(f"   -> {len(sh_jobs)} roles found.")
    all_jobs.extend(sh_jobs)

    print("4. Fetching Zoox (Autonomous Robotaxi)...", flush=True)
    zx_jobs = fetch_zoox()
    print(f"   -> {len(zx_jobs)} roles found.")
    all_jobs.extend(zx_jobs)

    print("5. Fetching Riot Games (AAA Gaming)...", flush=True)
    rg_jobs = fetch_riot_games()
    print(f"   -> {len(rg_jobs)} roles found.")
    all_jobs.extend(rg_jobs)

    print("6. Fetching Bungie (Destiny / Marathon)...", flush=True)
    bg_jobs = fetch_bungie()
    print(f"   -> {len(bg_jobs)} roles found.")
    all_jobs.extend(bg_jobs)

    print("7. Fetching Work With Indies (Indie Game Dev)...", flush=True)
    wwi_jobs = fetch_work_with_indies()
    print(f"   -> {len(wwi_jobs)} roles found.")
    all_jobs.extend(wwi_jobs)

    print("8. Fetching Remotive (Global Remote Tech)...", flush=True)
    rem_jobs = fetch_remotive()
    print(f"   -> {len(rem_jobs)} roles found.")
    all_jobs.extend(rem_jobs)

    print("9. Fetching Hasjob (India High-Signal Tech)...", flush=True)
    hj_jobs = fetch_hasjob()
    print(f"   -> {len(hj_jobs)} roles found.")
    all_jobs.extend(hj_jobs)

    print("10. Fetching Arbeitnow (Europe / DACH Tech)...", flush=True)
    an_jobs = fetch_arbeitnow()
    print(f"   -> {len(an_jobs)} roles found.")
    all_jobs.extend(an_jobs)

    print("11. Fetching Jobicy (EMEA & Middle East)...", flush=True)
    jb_jobs = fetch_jobicy_emea()
    print(f"   -> {len(jb_jobs)} roles found.")
    all_jobs.extend(jb_jobs)

    print(f"\nTotal Niche Jobs Gathered: {len(all_jobs)}. Ingesting into Supabase...", flush=True)
    saved = ingestor.batch_ingest_jobs(all_jobs)
    print(f"Successfully synced {saved} verified niche roles into database!", flush=True)

if __name__ == "__main__":
    ingest_all_niche_jobs()
