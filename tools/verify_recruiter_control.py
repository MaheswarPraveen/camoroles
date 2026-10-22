import urllib.request
import json

def test_endpoint(title, payload):
    print(f"\n=== Test: {title} ===")
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/ai/recruiter_chat',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    resp = urllib.request.urlopen(req, timeout=15)
    res = json.loads(resp.read().decode('utf-8'))
    print("Status:", resp.status)
    print("Reply:", res.get("reply"))
    print("Query:", res.get("query"))
    print("Discipline:", res.get("discipline"))
    print("Location:", res.get("location"))
    print("Has CV Request:", res.get("has_cv_request"))
    print("Has CV:", res.get("has_cv"))
    print("Total Matches:", res.get("total_matches"))
    matched = res.get("matched_jobs", [])
    print(f"Top Matched Jobs ({len(matched)}):")
    for j in matched:
        print(f"  - [{j.get('match_score')}% Match] {j.get('title')} @ {j.get('company')} ({j.get('location')}) -> {j.get('applyUrl')}")

# Test 1: Quantum Cryogenics
test_endpoint("Quantum Cryogenics", {
    "message": "show me quantum cryogenics hardware roles"
})

# Test 2: Confused without CV
test_endpoint("Confused without CV", {
    "message": "I'm confused , so give results based on cv"
})

# Test 3: Confused with CV
test_endpoint("Confused WITH Candidate CV", {
    "message": "I'm confused , so give results based on cv",
    "profile": {
        "headline": "Senior BCI Firmware & Neural Interface Engineer",
        "years_of_experience": 6,
        "experienceText": "6+ yrs",
        "skills": ["C++", "Firmware", "Electrophysiology", "FPGA", "Embedded Systems", "BCI"]
    }
})

# Test 4: Apple Hardware
test_endpoint("Apple Requisitions", {
    "message": "apple openings in electrical hardware"
})
