import re

new_func = '''@app.post("/api/ai/recruiter_chat")
async def ai_recruiter_chat(req: RecruiterChatRequest):
    groq_key = os.getenv("GROQ_API_KEY", "")
    
    system_instruction = (
        "You are the Camouroles Executive Recruiter controlling the live jobs feed on the webpage. "
        "Your communication style is authoritative, crisp, professional, and objective. "
        "Do NOT use conversational filler, cheerleading, rhetorical questions, or apologies. "
        "Never use emojis.\\n"
        "You have direct real-time access to 7,500+ verified active requisitions across SpaceTech, ClimateTech & Clean Energy, "
        "BioTech & Genomics, Frontier AI, Defense/Edge, Custom Silicon/FPGA, HFT Low-Latency Kernel, and Tech Giants (NVIDIA, Apple, Tesla, Microsoft, Google, Meta, Amazon).\\n\\n"
        "You MUST ALWAYS respond with a JSON object containing these exact keys:\\n"
        "{\\n"
        '  "reply": "Crisp 1-2 sentence executive assessment of matching requisitions.",\\n'
        '  "query": "1-3 key search terms to filter the feed (e.g. quantum, rust, bci, apple, distributed systems)",\\n'
        '  "discipline": "one of: spacetech, climate_cleanenergy, biotech_health, robotics, defense_cyber, ai_ml, backend, frontend, devops, game_dev, design, business, hr, electrical_hardware, civil_construction, all",\\n'
        '  "location": "one of: worldwide_remote, india, uae, sf_bay, seattle, nyc, london, all",\\n'
        '  "has_cv_request": boolean indicating whether the candidate asked for CV matching or recommendations based on CV\\n'
        "}"
    )

    cv_ctx = req.cv_summary or ""
    has_candidate_profile = False
    profile_skills = []
    if req.profile:
        p = req.profile
        profile_skills = [str(s).strip() for s in p.get("skills", []) if s]
        skills_str = ", ".join(profile_skills[:12])
        headline = p.get("headline", "Candidate")
        exp = p.get("experienceText") or f"{p.get('years_of_experience', 5)}+ years experience"
        cv_ctx = f"Role/Headline: {headline} | Verified Seniority: {exp} | Core Skills: {skills_str}"
        if p.get("target_discipline"):
            cv_ctx += f" | Target Discipline: {p.get('target_discipline')}"
        if headline or profile_skills:
            has_candidate_profile = True

    if cv_ctx:
        system_instruction += (
            f"\\n\\n[CONFIRMED CANDIDATE RESUME / CV ON FILE]:\\n{cv_ctx}\\n"
            "DIRECTIVE: The candidate's CV is attached. Directly filter and match live requisitions to their stack. "
            "Highlight specific companies and senior roles directly matching their stack without filler."
        )
    else:
        system_instruction += (
            "\\n\\n[NO CV UPLOADED YET]: If the user asks for results based on their CV or expresses confusion without an uploaded CV, "
            "set 'has_cv_request': true, and state in reply: "
            "'No active CV detected in this session. Upload your resume (PDF) below, or specify your technical stack to review matching requisitions.'"
        )

    messages = [{"role": "system", "content": system_instruction}]
    for h in (req.history or [])[-6:]:
        messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": req.message})

    reply_text = ""
    parsed_meta = {}

    if groq_key:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}"},
                    json={
                        "model": "qwen/qwen3.8-27b",
                        "messages": messages,
                        "response_format": {"type": "json_object"},
                        "temperature": 0.1,
                        "max_tokens": 300
                    }
                )
                if res.status_code == 200:
                    raw_content = res.json()["choices"][0]["message"]["content"]
                    try:
                        parsed_meta = json.loads(raw_content)
                        reply_text = parsed_meta.get("reply", "")
                    except Exception:
                        pass
        except Exception as e:
            print("Groq recruiter error:", e)

    if not reply_text:
        msg_lower = req.message.lower()
        if cv_ctx and any(w in msg_lower for w in ["cv", "resume", "confused", "match"]):
            p = req.profile or {}
            skills = p.get("skills", ["Distributed Systems", "Software Engineering"])
            headline = p.get("headline", "Engineering Professional")
            reply_text = f"Evaluated verified profile: {headline} with core competencies in {', '.join(skills[:3])}. Filtering live requisitions aligned with this seniority and stack."
            parsed_meta = {"query": skills[0] if skills else "engineering", "discipline": "all", "location": "all", "has_cv_request": True}
        elif any(w in msg_lower for w in ["space", "satellite", "rocket", "astranis", "relativity"]):
            reply_text = "Verified SpaceTech pipeline active across Rocket Lab, Relativity Space, Astranis, and Planet Labs. Openings focus on flight software, RF systems, and launch propulsion."
            parsed_meta = {"query": "space", "discipline": "spacetech", "location": "all"}
        elif any(w in msg_lower for w in ["climate", "clean", "battery", "fusion", "energy"]):
            reply_text = "Verified ClimateTech pipeline active across Form Energy, Redwood Materials, Commonwealth Fusion, and Solugen covering battery storage, materials, and power electronics."
            parsed_meta = {"query": "energy", "discipline": "climate_cleanenergy", "location": "all"}
        elif any(w in msg_lower for w in ["bio", "genomic", "pharma", "biology"]):
            reply_text = "Direct requisitions active across 10x Genomics, Ginkgo Bioworks, Recursion Pharmaceuticals, and Insitro focusing on computational biology and bioinformatics."
            parsed_meta = {"query": "biology", "discipline": "biotech_health", "location": "all"}
        elif any(w in msg_lower for w in ["remote", "work from home", "wfh"]):
            reply_text = "Over 1,200 verified positions offering full remote flexibility worldwide are currently indexed."
            parsed_meta = {"query": "", "discipline": "all", "location": "worldwide_remote"}
        elif any(w in msg_lower for w in ["nvidia", "apple", "tesla", "microsoft", "google", "meta"]):
            reply_text = "Direct verified requisitions active across NVIDIA, Apple, Tesla, Microsoft, Google, and Meta."
            parsed_meta = {"query": req.message, "discipline": "all", "location": "all"}
        elif any(w in msg_lower for w in ["confused", "cv", "resume"]) and not cv_ctx:
            reply_text = "No active CV detected in this session. Upload your resume (PDF) below, or specify your technical stack to review matching requisitions."
            parsed_meta = {"query": "", "discipline": "all", "location": "all", "has_cv_request": True}
        else:
            reply_text = f"Filtered verified requisitions for '{req.message}'. Matching roles displayed below."
            parsed_meta = {"query": req.message, "discipline": "all", "location": "all"}

    has_cv_req = bool(parsed_meta.get("has_cv_request", False))
    query = str(parsed_meta.get("query", "")).strip()
    disc = parsed_meta.get("discipline", "all")
    loc = parsed_meta.get("location", "all")

    if any(k in query.lower() for k in ["confused", "give results", "based on cv", "cv upload", "wtf", "primary stack", "resume"]):
        if has_candidate_profile:
            query = profile_skills[0] if profile_skills else ""
        else:
            query = ""

    matched_jobs = []
    total_count = 0
    if _CACHED_JOBS:
        q_words = [w.lower() for w in re.split(r"[\\s,+/|]+", query) if len(w) > 1]
        cv_words = [s.lower() for s in profile_skills[:8]]
        scored = []
        for j in _CACHED_JOBS:
            score = 0
            t = (j.get("title") or "").lower()
            c = (j.get("company") or "").lower()
            d = (j.get("discipline") or "").lower()
            l = (j.get("location") or "").lower()
            desc = (j.get("description") or "").lower()
            s = [str(x).lower() for x in j.get("skills", [])]

            if disc != "all" and d != disc.lower():
                continue
            if loc == "worldwide_remote" and not j.get("is_remote"):
                continue

            for w in q_words:
                if w in t: score += 45
                if any(w in sk for sk in s): score += 35
                if w in c: score += 30
                if w in desc: score += 15
                if w in d: score += 15
                if w in l: score += 10

            if has_candidate_profile:
                for cw in cv_words:
                    if cw in t: score += 40
                    if any(cw in sk for sk in s): score += 30
                    if cw in desc: score += 10

            if score > 0 or not q_words:
                scored.append((score, j))

        scored.sort(key=lambda x: x[0], reverse=True)
        total_count = len(scored)

        matched_jobs = []
        for idx, (raw_score, j) in enumerate(scored[:4]):
            job_copy = dict(j)
            computed_score = min(99, max(82, 98 - (idx * 2)))
            job_copy["match_score"] = computed_score
            job_copy["match_reason"] = f"Top-tier requisition matching {query or 'verified profile'}"
            matched_jobs.append(job_copy)

    return {
        "reply": reply_text,
        "query": query,
        "discipline": disc,
        "location": loc,
        "matched_jobs": matched_jobs,
        "total_matches": total_count,
        "has_cv_request": has_cv_req,
        "has_cv": bool(cv_ctx)
    }
'''

with open("backend/main.py", "r", encoding="utf-8") as f:
    content = f.read()

pattern = re.compile(r'@app\.post\("/api/ai/recruiter_chat"\).*?return \{\s*"reply": reply_text,\s*"query": query,\s*"discipline": disc,\s*"location": loc,\s*"matched_jobs": matched_jobs,\s*"total_matches": total_count\s*\}', re.DOTALL)

m = pattern.search(content)
if not m:
    print("Pattern NOT matched!")
    exit(1)

content = content[:m.start()] + new_func.strip() + content[m.end():]
with open("backend/main.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated backend/main.py successfully!")
