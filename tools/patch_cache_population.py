with open("backend/main.py", "r", encoding="utf-8") as f:
    content = f.read()

old_block = '''    matched_jobs = []
    total_count = 0
    if _CACHED_JOBS:'''

new_block = '''    matched_jobs = []
    total_count = 0
    global _CACHED_JOBS
    if not _CACHED_JOBS:
        try:
            get_jobs_spec()
        except Exception as e:
            print("Failed to auto-populate _CACHED_JOBS:", e)

    if _CACHED_JOBS:'''

content = content.replace(old_block, new_block, 1)

old_loc = '''            if loc == "worldwide_remote" and not j.get("is_remote"):
                continue'''

new_loc = '''            if loc == "worldwide_remote" and not (j.get("is_remote") or "remote" in l or "worldwide" in l):
                continue
            elif loc == "india" and not any(k in l for k in ["india", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "delhi"]):
                continue
            elif loc == "uae" and not any(k in l for k in ["uae", "dubai", "abu dhabi"]):
                continue'''

content = content.replace(old_loc, new_loc, 1)

with open("backend/main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated cache auto-population and location logic in backend/main.py")
