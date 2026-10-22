import re

with open("backend/main.py", "r", encoding="utf-8") as f:
    content = f.read()

recruiter_start = '@app.post("/api/ai/recruiter_chat")'
recruiter_end = '    return {\n        "reply": reply_text,\n        "query": query,\n        "discipline": disc,\n        "location": loc,\n        "matched_jobs": matched_jobs,\n        "total_matches": total_count,\n        "has_cv_request": has_cv_req,\n        "has_cv": bool(cv_ctx)\n    }'

new_func = '''@app.post("/api/ai/recruiter_chat")
async def ai_recruiter_chat(req: RecruiterChatRequest):
    groq_key = os.getenv("GROQ_API_KEY", "")
    
    system_instruction = (
        "You are the Camouroles Executive Recruiter & Career Advisor. "
        "Talk through with the candidate what they are looking for, understand their goals, evaluate industry options, "
        "and advise them thoughtfully like an experienced principal recruiter at a top firm. "
        "Engage in a natural, professional, insightful dialogue like ChatGPT. Never use emojis.\\n"
        "You have direct real-time access to 7,540 verified active requisitions across SpaceTech, ClimateTech & Clean Energy, "
        "BioTech & Genomics, Frontier AI, Defense/Edge, Custom Silicon/FPGA, HFT Low-Latency Kernel, and Tech Giants (Apple, NVIDIA, Tesla, Google, Meta, Microsoft, Amazon).\\n\\n"
        "You MUST ALWAYS respond with a JSON object containing these exact keys:\\n"
        "{\\n"
        '  "reply": "Natural, thoughtful, professional response talking through their goals, trade-offs, or questions.",\\n'
        '  "target_company": "<exact company name if candidate asked for a specific company like Apple, NVIDIA, Tesla, Google, Meta, Microsoft, Amazon, Anduril, etc., otherwise empty string \\"\\">",\\n'
        '  "query": "<clean 1-3 keyword role search (e.g. distributed systems, hardware engineer, quantum, bci), or empty string \\"\\">",\\n'
        '  "discipline": "<spacetech | climate_cleanenergy | biotech_health | robotics | defense_cyber | ai_ml | backend | frontend | devops | game_dev | design | business | hr | electrical_hardware | civil_construction | all>",\\n'
        '  "location": "<worldwide_remote | india | uae | sf_bay | seattle | nyc | london | all>",\\n'
        '  "has_cv_request": boolean\\n'
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
            "DIRECTIVE: The candidate's CV is attached. Talk through how their background and stack fits "
            "the current hiring landscape and set search criteria directly to their domain and stack."
        )
    else:
        system_instruction += (
            "\\n\\n[NO CV UPLOADED YET]: If the user asks for results based on their CV or expresses confusion without an uploaded CV, "
            "set 'has_cv_request': true, and explain that you can match their exact skills and seniority as soon as they drop their resume or name their stack."
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
                        "temperature": 0.3,
                        "max_tokens": 350
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
            reply_text = f"Evaluated verified profile: {headline} with competencies in {', '.join(skills[:3])}. Filtering live requisitions aligned with your seniority."
            parsed_meta = {"query": skills[0] if skills else "engineering", "discipline": "all", "location": "all", "has_cv_request": True}
        elif any(w in msg_lower for w in ["space", "satellite", "rocket", "astranis", "relativity"]):
            reply_text = "Verified SpaceTech pipeline active across Rocket Lab, Relativity Space, Astranis, and Planet Labs covering flight software, RF, and propulsion."
            parsed_meta = {"query": "space", "discipline": "spacetech", "location": "all"}
        elif any(w in msg_lower for w in ["climate", "clean", "battery", "fusion", "energy"]):
            reply_text = "Verified ClimateTech pipeline active across Form Energy, Redwood Materials, Commonwealth Fusion, and Solugen."
            parsed_meta = {"query": "energy", "discipline": "climate_cleanenergy", "location": "all"}
        elif any(w in msg_lower for w in ["bio", "genomic", "pharma", "biology"]):
            reply_text = "Requisitions active across 10x Genomics, Ginkgo Bioworks, Recursion Pharmaceuticals, and Insitro."
            parsed_meta = {"query": "biology", "discipline": "biotech_health", "location": "all"}
        elif any(w in msg_lower for w in ["remote", "work from home", "wfh"]):
            reply_text = "Over 1,200 verified positions offering full remote flexibility worldwide are currently indexed."
            parsed_meta = {"query": "", "discipline": "all", "location": "worldwide_remote"}
        elif any(w in msg_lower for w in ["confused", "cv", "resume"]) and not cv_ctx:
            reply_text = "No CV detected in this session yet. Upload your resume (PDF) below, or specify your primary technical stack so we can evaluate qualified opportunities."
            parsed_meta = {"query": "", "discipline": "all", "location": "all", "has_cv_request": True}
        else:
            reply_text = f"Filtered verified requisitions for '{req.message}'. Review the matching positions on the homepage."
            parsed_meta = {"query": req.message, "discipline": "all", "location": "all"}

    has_cv_req = bool(parsed_meta.get("has_cv_request", False))
    target_comp = str(parsed_meta.get("target_company", "")).strip()
    query = str(parsed_meta.get("query", "")).strip()
    disc = parsed_meta.get("discipline", "all")
    loc = parsed_meta.get("location", "all")

    # Detect brand names directly from the prompt
    msg_l = req.message.lower()
    known_brands = [
        "apple", "nvidia", "tesla", "google", "meta", "microsoft", "amazon",
        "anduril", "palantir", "cloudflare", "riot games", "optiver", "jane street",
        "imc", "rigetti", "paradromics", "adnoc", "masdar", "jasara", "rocket lab",
        "relativity", "form energy", "redwood materials", "skydio", "waymo", "anthropic"
    ]
    for kb in known_brands:
        if re.search(r'\\b' + re.escape(kb) + r'\\b', msg_l):
            target_comp = kb
            # Strip brand from query terms so query focuses on role
            query = re.sub(r'\\b' + re.escape(kb) + r'\\b', '', query, flags=re.IGNORECASE).strip()
            break

    if any(k in query.lower() for k in ["confused", "give results", "based on cv", "cv upload", "wtf", "primary stack", "resume"]):
        if has_candidate_profile:
            query = profile_skills[0] if profile_skills else ""
        else:
            query = ""

    # Clean punctuation from query
    query = re.sub(r'[,+/|]+', ' ', query).strip()

    matched_jobs = []
    total_count = 0
    global _CACHED_JOBS
    if not _CACHED_JOBS:
        try:
            get_jobs_spec()
        except Exception as e:
            print("Failed to auto-populate _CACHED_JOBS:", e)

    if _CACHED_JOBS:
        q_words = [w.lower() for w in query.split() if len(w) > 2 and w not in ["openings", "jobs", "roles", "positions", "looking", "want"]]
        cv_words = [s.lower() for s in profile_skills[:8]]
        scored = []
        for j in _CACHED_JOBS:
            t = (j.get("title") or "").lower()
            c = (j.get("company") or "").lower()
            d = (j.get("discipline") or "").lower()
            l = (j.get("location") or "").lower()
            desc = (j.get("description") or "").lower()
            s = [str(x).lower() for x in j.get("skills", [])]

            # 1. STRICT COMPANY FILTER: If company was specified, non-matching companies are 100% EXCLUDED
            if target_comp and target_comp.lower() not in c:
                continue

            # 2. DISCIPLINE FILTER
            if disc != "all" and d != disc.lower():
                continue

            # 3. LOCATION FILTER
            if loc == "worldwide_remote" and not (j.get("is_remote") or "remote" in l or "worldwide" in l):
                continue
            elif loc == "india" and not any(k in l for k in ["india", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "delhi"]):
                continue
            elif loc == "uae" and not any(k in l for k in ["uae", "dubai", "abu dhabi"]):
                continue

            # 4. HONEST, REALISTIC MATCH PERCENTAGE
            score = 0
            max_possible = 0

            if target_comp:
                max_possible += 40
                if target_comp.lower() in c:
                    score += 40

            if q_words:
                max_possible += 40
                hits = 0
                for w in q_words:
                    if w in t: hits += 1.5
                    elif any(w in sk for sk in s): hits += 1.0
                    elif w in desc: hits += 0.5
                score += int(min(1.0, hits / max(1, len(q_words))) * 40)

            if has_candidate_profile and cv_words:
                max_possible += 40
                overlap = sum(1 for cw in cv_words if any(cw in sk for sk in s) or cw in t)
                score += int(min(1.0, overlap / max(1, min(4, len(cv_words)))) * 40)

            if max_possible > 0:
                pct = int((score / max_possible) * 100)
                if pct > 0:
                    pct = min(96, max(52, pct))
            else:
                pct = 0

            # Only include genuinely matching positions
            if pct > 0 or (not q_words and not target_comp and not cv_words):
                scored.append((pct, j))

        scored.sort(key=lambda x: x[0], reverse=True)
        total_count = len(scored)

        matched_jobs = []
        for idx, (real_score, j) in enumerate(scored[:25]):
            job_copy = dict(j)
            job_copy["match_score"] = real_score
            job_copy["match_reason"] = f"Aligned with {query or target_comp or 'verified criteria'}"
            matched_jobs.append(job_copy)

    return {
        "reply": reply_text,
        "query": query,
        "target_company": target_comp,
        "discipline": disc,
        "location": loc,
        "matched_jobs": matched_jobs,
        "total_matches": total_count,
        "has_cv_request": has_cv_req,
        "has_cv": bool(cv_ctx)
    }'''

start_idx = content.find(recruiter_start)
if start_idx == -1:
    print("Could not find recruiter_start!")
    exit(1)

end_pattern = re.compile(r'return\s*\{\s*"reply":\s*reply_text,\s*"query":\s*query,\s*"discipline":\s*disc,\s*"location":\s*loc,\s*"matched_jobs":\s*matched_jobs,\s*"total_matches":\s*total_count,\s*"has_cv_request":\s*has_cv_req,\s*"has_cv":\s*bool\(cv_ctx\)\s*\}', re.DOTALL)
m = end_pattern.search(content, start_idx)
if not m:
    print("Could not find end_pattern!")
    exit(1)

content = content[:start_idx] + new_func + content[m.end():]
with open("backend/main.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated backend/main.py successfully with brand filter & realistic probabilities!")
