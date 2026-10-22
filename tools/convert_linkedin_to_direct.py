"""
Update Supabase to replace LinkedIn URLs for major companies with direct company portals.
"""

import os, re
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(".dev.vars")
load_dotenv("backend/.env")
load_dotenv(".env")

url = os.getenv("SUPABASE_URL", "https://xteoktfzftqybflpubvo.supabase.co")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
sb = create_client(url, key)

print("Connected to Supabase. Fetching LinkedIn jobs...")

# Fetch all jobs with linkedin in apply_url
res = sb.table("jobs").select("id,title,company,apply_url").ilike("apply_url", "%linkedin%").execute()
jobs = res.data or []
print(f"Total jobs with LinkedIn URL: {len(jobs)}")

updated = 0
for j in jobs:
    comp = (j.get("company") or "").lower()
    title = j.get("title") or ""
    t_enc = title.replace(" ", "%20").replace("&", "%26")
    new_url = None
    portal = "direct"

    if "nvidia" in comp:
        new_url = f"https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite?q={t_enc}"
        portal = "workday"
    elif "apple" in comp:
        new_url = f"https://jobs.apple.com/en-us/search?search={t_enc}"
        portal = "apple"
    elif "meta" in comp or "facebook" in comp:
        new_url = f"https://www.metacareers.com/jobs?q={t_enc}"
        portal = "meta"
    elif "google" in comp or "alphabet" in comp or "waymo" in comp:
        new_url = f"https://www.google.com/about/careers/applications/jobs/results/?q={t_enc}"
        portal = "google"
    elif "microsoft" in comp:
        new_url = f"https://jobs.careers.microsoft.com/global/en/search?q={t_enc}"
        portal = "microsoft"
    elif "tesla" in comp:
        new_url = f"https://www.tesla.com/careers/search/?query={t_enc}"
        portal = "tesla"

    if new_url and new_url != j.get("apply_url"):
        try:
            sb.table("jobs").update({"apply_url": new_url, "ats_type": "direct"}).eq("id", j["id"]).execute()
            updated += 1
        except Exception as e:
            print(f"Error updating {j['id']}: {e}")

print(f"Successfully converted {updated} major brand LinkedIn URLs to official direct ATS portals!")
