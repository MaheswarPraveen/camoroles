import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()
groq_key = os.getenv("GROQ_API_KEY", "")

cv_profile = {
    "headline": "Senior Staff Distributed Systems & Kernel Engineer",
    "years_of_experience": 8,
    "experienceText": "8+ yrs experience",
    "skills": ["Rust", "Distributed Systems", "Linux Kernel", "DPDK", "C++", "eBPF", "Raft"]
}

def test_query(prompt, profile=None):
    system_content = (
        "You are the Camouroles Executive Recruiter controlling the live jobs feed on the webpage. "
        "Your role is authoritative, crisp, professional, and objective. "
        "Do NOT ask rhetorical questions, do NOT use cheerleading or conversational fluff. Never use emojis.\n"
        "You have direct real-time access to 7,500+ verified active requisitions across SpaceTech, ClimateTech, "
        "BioTech & Genomics, Frontier AI, Defense/Edge, Custom Silicon/FPGA, HFT Kernel, and Tech Giants.\n\n"
        "Always respond with a valid JSON object with these exact keys:\n"
        "{\n"
        '  "reply": "Crisp 1-2 sentence executive assessment of matching live requisitions.",\n'
        '  "query": "1-3 key search terms to filter the feed (e.g. distributed systems, rust, bci, quantum, apple)",\n'
        '  "discipline": "one of: spacetech, climate_cleanenergy, biotech_health, robotics, defense_cyber, ai_ml, backend, frontend, devops, game_dev, design, business, hr, electrical_hardware, civil_construction, all",\n'
        '  "location": "one of: worldwide_remote, india, uae, sf_bay, seattle, nyc, london, all",\n'
        '  "has_cv_request": boolean indicating whether the candidate asked for CV matching or recommendations based on CV\n'
        "}\n"
    )

    if profile:
        skills_str = ", ".join(profile.get("skills", [])[:10])
        headline = profile.get("headline", "Candidate")
        exp = profile.get("experienceText", "Senior")
        system_content += f"\n[CONFIRMED CANDIDATE CV ON FILE]: Headline: {headline} | Seniority: {exp} | Stack: {skills_str}\n"
        system_content += "DIRECTIVE: Candidate CV is verified. Directly filter and match live requisitions to their stack.\n"
    else:
        system_content += "\n[NO CV UPLOADED YET]: If candidate asks for CV matching or expresses confusion without a CV, set 'has_cv_request': true, and explain that you are ready to evaluate their background as soon as they drop their resume or state their primary stack.\n"

    payload = {
        "model": "qwen/qwen3.8-27b",
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 250
    }

    r = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {groq_key}"},
        json=payload,
        timeout=10.0
    )
    print(f"\n--- Query: {prompt} (With CV: {bool(profile)}) ---")
    print(r.json()['choices'][0]['message']['content'])

test_query("I'm confused , so give results based on cv", profile=cv_profile)
test_query("I'm confused , so give results based on cv", profile=None)
test_query("what do you think is better", profile=cv_profile)
test_query("nvidia openings", profile=None)
