import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("backend/.env")
load_dotenv(".env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
db = create_client(url, key)

res = db.table("jobs").select("id", count="exact").eq("is_active", True).execute()
print(f"Total Active Jobs in Supabase: {res.count}")

keywords = ["quantum", "neuralink", "saildrone", "fusion", "tenstorrent", "jane street", "matter labs", "masdar", "bechtel"]
for kw in keywords:
    r1 = db.table("jobs").select("title, company").eq("is_active", True).ilike("title", f"%{kw}%").execute()
    r2 = db.table("jobs").select("title, company").eq("is_active", True).ilike("company", f"%{kw}%").execute()
    total = len(set([x["title"] for x in (r1.data or []) + (r2.data or [])]))
    print(f"Keyword '{kw}': {total} matching active roles")
