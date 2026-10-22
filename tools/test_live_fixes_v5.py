import httpx
import json

URL = "https://camouroles.primemax.workers.dev/api/ai/recruiter_chat"

# Junior profile (1 year experience)
junior_profile = {
    "headline": "Robotics and AI Research Engineer",
    "experienceYears": 1,
    "experienceText": "1+ yrs verified experience",
    "skills": ["Python", "C/C++", "ROS 2", "ArduPilot", "PyTorch", "OpenCV"],
    "discipline": "robotics"
}

def send_chat(msg, conversation):
    payload = {
        "message": msg,
        "conversation": conversation,
        "profile": junior_profile,
        "cv_summary": "Robotics and AI Research Engineer (1+ yrs verified experience) - Core Skills: Python, C/C++, ROS 2, ArduPilot, PyTorch, OpenCV"
    }
    r = httpx.post(URL, json=payload, timeout=25.0)
    print(f"Status: {r.status_code}")
    data = r.json()
    print("REPLY:\n", data.get("reply"))
    print("FILTERS:", json.dumps(data.get("filters"), indent=2))
    print(f"TOTAL MATCHED: {data.get('total_matched')}")
    print("MATCHED IDs (first 5):", data.get("matched_job_ids", [])[:5])
    print("=" * 60)
    return data

def main():
    history = []

    print("--- TURN 1: Initial query (Robotics worldwide remote) ---")
    d1 = send_chat("can we have some remote jobs?", history)
    history.append({"role": "user", "content": "can we have some remote jobs?"})
    history.append({"role": "assistant", "content": d1.get("reply", "")})

    print("--- TURN 2: Pivot to UAE Safety (Must reset remote and company, search whole again!) ---")
    d2 = send_chat("where's the jobs from uae for safety", history)
    history.append({"role": "user", "content": "where's the jobs from uae for safety"})
    history.append({"role": "assistant", "content": d2.get("reply", "")})

    print("--- TEST CV MATCHING SENIORITY ON JUNIOR CV ---")
    r = httpx.post("https://camouroles.primemax.workers.dev/api/cv/match", json={
        "cv_text": "Robotics and AI Research Engineer with 1 year experience building autonomous rovers with Python, C++, ROS 2, ArduPilot, OpenCV.",
        "file_name": "Junior_Robotics_CV.pdf"
    }, timeout=25.0)
    match_data = r.json()
    print("Parsed Profile:", json.dumps(match_data.get("profile"), indent=2))
    top_matches = match_data.get("matches", {})
    print(f"Total scored matches: {len(top_matches)}")
    # Fetch job details to verify top matches aren't Senior/Staff
    jobs_res = httpx.get("https://camouroles.primemax.workers.dev/api/jobs", timeout=25.0)
    all_jobs = {j["id"]: j for j in jobs_res.json().get("jobs", [])}
    sorted_matches = sorted(top_matches.items(), key=lambda x: x[1]["score"], reverse=True)[:5]
    print("\nTop 5 Scored Matches for 1 YOE Candidate:")
    for jid, m in sorted_matches:
        j = all_jobs.get(jid, {})
        print(f"- {j.get('title')} at {j.get('company')} (Exp: {j.get('expText')}) -> Score: {m['score']}%")

if __name__ == "__main__":
    main()
