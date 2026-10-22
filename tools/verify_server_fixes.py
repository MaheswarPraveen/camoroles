import urllib.request
import json

print("=== 1. Testing /api/jobs ===")
try:
    with urllib.request.urlopen("http://127.0.0.1:8000/api/jobs", timeout=20) as resp:
        data = json.loads(resp.read().decode())
        jobs = data.get("jobs", [])
        print(f"Total jobs in feed: {len(jobs)}")
        for brand in ["NVIDIA", "Apple", "Tesla", "Microsoft", "Google", "Meta"]:
            brand_jobs = [j for j in jobs if brand.lower() in j.get("company", "").lower()]
            print(f"  {brand}: {len(brand_jobs)} live roles")
            if brand_jobs:
                print(f"    Sample: {brand_jobs[0]['title']} -> {brand_jobs[0].get('apply_url')}")
except Exception as e:
    print("API jobs error:", e)

print("\n=== 2. Testing /api/ai/recruiter_chat with CV Profile ===")
try:
    payload = {
        "message": "I'm confused , so give results based on cv",
        "history": [],
        "profile": {
            "headline": "Senior Distributed Systems & AI Engineer",
            "experienceText": "6+ years verified engineering experience",
            "skills": ["Distributed Systems", "PyTorch", "Python", "Kubernetes", "C++"]
        }
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/ai/recruiter_chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
        print("AI Reply:")
        print(" ", data.get("reply"))
        print("Criteria:", data.get("criteria"))
except Exception as e:
    print("Recruiter chat error:", e)
