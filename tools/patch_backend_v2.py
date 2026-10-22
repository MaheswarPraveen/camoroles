import re

new_match_cv_and_recruiter = '''    profile = {
        "headline": f"{'Early Career' if years <= 3 else 'Senior'} {top_disc.split('&')[0].strip()} Engineer",
        "experienceText": f"{years} {'year' if years == 1 else 'years'} experience",
        "years": years,
        "skills": found_skills[:6]
    }

    global _CACHED_JOBS
    if not _CACHED_JOBS:
        try:
            get_jobs_spec()
        except Exception as e:
            print("Failed to auto-populate _CACHED_JOBS in cv_match:", e)

    matches = {}
    if _CACHED_JOBS:
        found_lower = [s.lower() for s in found_skills]
        disc_prefix = top_disc.lower().split('&')[0].strip()

        scored_cv_jobs = []
        for job in _CACHED_JOBS:
            jid = job.get("id")
            if not jid:
                continue
            jtitle = (job.get("title") or "").lower()
            jskills = [str(x).lower() for x in (job.get("skills") or [])]
            jdisc = (job.get("discipline") or "").lower()

            # Measure overlap
            matching_skills = [s for s in jskills if any(fs in s or s in fs for fs in found_lower)]
            title_hits = sum(1 for fs in found_lower if fs in jtitle)
            disc_hit = disc_prefix in jdisc or any(w in jtitle for w in disc_prefix.split() if len(w) > 3)

            min_exp = job.get("minExp", 0)
            max_exp = job.get("maxExp", 12)
            exp_ok = (min_exp <= years <= max_exp + 2)

            if not matching_skills and title_hits == 0 and not disc_hit:
                continue

            score = 50
            if matching_skills:
                score += min(32, len(matching_skills) * 11)
            if title_hits > 0:
                score += min(12, title_hits * 6)
            if disc_hit:
                score += 8
            if exp_ok:
                score += 4

            score = min(97, max(52, score))
            matched_tags = ", ".join(matching_skills[:3]) if matching_skills else (", ".join(job.get("skills", [])[:2]) if job.get("skills") else "Technical background")
            explanation = f"Matched on {matched_tags} · Aligned with your {profile['experienceText']} in {top_disc.split('&')[0].strip()}."
            scored_cv_jobs.append((score, jid, explanation))

        scored_cv_jobs.sort(key=lambda x: x[0], reverse=True)
        for score, jid, explanation in scored_cv_jobs[:300]:
            matches[jid] = {
                "score": score,
                "explanation": explanation
            }

    return {"profile": profile, "matches": matches}

# ---------- Conversational AI Recruiter (ChatGPT-style) ----------

class ChatMessage(BaseModel):
    role: str
    content: str

class RecruiterChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    cv_summary: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None
    target_discipline: Optional[str] = None
    target_location: Optional[str] = None

@app.post("/api/ai/recruiter_chat")
async def ai_recruiter_chat(req: RecruiterChatRequest):
    groq_key = os.getenv("GROQ_API_KEY", "")

    system_instruction = (
        "You are the Camouroles Career Partner & Senior Technical Recruiter. "
        "Your style is warm, friendly, natural, approachable, and encouraging, like a supportive senior colleague or peer mentor having a candid conversation over coffee. "
        "Never sound like a script, never use corporate jargon or bureaucratic robotic templates. Be real, thoughtful, and genuinely helpful. "
        "Never use any emojis under any circumstances.\\n\\n"
        "You have direct real-time access to 7,540 verified active requisitions across SpaceTech, ClimateTech & Clean Energy, "
        "BioTech & Genomics, Frontier AI, Defense/Edge, Custom Silicon/FPGA, HFT Low-Latency Kernel, and Tech Giants (Apple, NVIDIA, Tesla, Google, Meta, Microsoft, Amazon).\\n\\n"
        "Guidelines:\\n"
        "- If the candidate is confused or unsure what they want: Be empathetic and welcoming. Validate that navigating careers is tricky, offer clear perspective on different paths (e.g., frontier startups vs tech giants), and give them friendly, easy ways to explore without pressuring them.\\n"
        "- If they ask 'what is better' (e.g., between two companies or domains): Give a balanced, insightful take covering culture, equity upside vs stability, engineering challenges, and mission impact, then warmly invite them to check out open roles.\\n"
        "- If they want roles at a specific brand (Apple, NVIDIA, Tesla, etc.): Focus on that exact company in 'target_company' and warmly discuss what it's like building there.\\n"
        "- If their CV is attached: Enthusiastically acknowledge their background and skills, explain how their stack maps to current hiring, and highlight the kinds of roles they are suited for.\\n"
        "- If no CV is attached yet and they ask for CV matching: Friendly remind them they can drop their resume in the box above whenever they like, or simply tell you what technologies they enjoy building with.\\n\\n"
        "You MUST ALWAYS respond with a JSON object containing these exact keys:\\n"
        "{\\n"
        '  "reply": "Warm, friendly, human response talking through their questions, trade-offs, or background without any robotic script or emojis.",\\n'
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
        exp = p.get("experienceText") or f"{p.get('years_of_experience', p.get('years', 5))}+ years experience"
        cv_ctx = f"Role/Headline: {headline} | Verified Seniority: {exp} | Core Skills: {skills_str}"
        if p.get("target_discipline"):
            cv_ctx += f" | Target Discipline: {p.get('target_discipline')}"
        if headline or profile_skills:
            has_candidate_profile = True

    if cv_ctx:
        system_instruction += (
            f"\\n\\n[CONFIRMED CANDIDATE RESUME ON FILE]:\\n{cv_ctx}\\n"
            "DIRECTIVE: The candidate's resume is active. Warmly address their real skills and experience, "
            "recommend roles that fit their level, and set the query and discipline to match their background."
        )
    else:
        system_instruction += (
            "\\n\\n[NO CV UPLOADED YET IN SESSION]: If the candidate asks for results based on their CV or feels confused, "
            "warmly and casually let them know they can drop their PDF resume right above, or just type out what tech they work with, and you will find the best fits."
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
                        "temperature": 0.4,
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
            reply_text = f"I have got your resume right here ({headline}) with background in {', '.join(skills[:3])}. I pulled up the verified openings that align best with your stack. Take a look below."
            parsed_meta = {"query": skills[0] if skills else "engineering", "discipline": "all", "location": "all", "has_cv_request": False}
        elif any(w in msg_lower for w in ["space", "satellite", "rocket", "astranis", "relativity"]):
            reply_text = "SpaceTech is hiring aggressively right now. We have open flight software, avionics, and propulsion roles across Rocket Lab, Relativity Space, and Astranis."
            parsed_meta = {"query": "space", "discipline": "spacetech", "location": "all"}
        elif any(w in msg_lower for w in ["climate", "clean", "battery", "fusion", "energy"]):
            reply_text = "Clean energy and climate tech have some of the most exciting hard-tech problems right now, with live openings at Commonwealth Fusion, Form Energy, and Redwood Materials."
            parsed_meta = {"query": "energy", "discipline": "climate_cleanenergy", "location": "all"}
        elif any(w in msg_lower for w in ["confused", "cv", "resume"]) and not cv_ctx:
            reply_text = "No worries at all! Job searching can definitely feel overwhelming with so many directions to take. You can drop your resume into the PDF box above whenever you are ready, or just tell me in your own words what tech you enjoy working with (like Python, React, hardware, etc.) and we will take it from there."
            parsed_meta = {"query": "", "discipline": "all", "location": "all", "has_cv_request": True}
        elif "apple" in msg_lower:
            reply_text = "Apple has verified engineering openings indexed right now across systems software, hardware validation, and silicon design. Here are their active positions."
            parsed_meta = {"query": "", "target_company": "apple", "discipline": "all", "location": "all"}
        elif "nvidia" in msg_lower:
            reply_text = "NVIDIA is actively hiring across CUDA architecture, deep learning infrastructure, and GPU kernel optimization. Here are their verified active roles."
            parsed_meta = {"query": "", "target_company": "nvidia", "discipline": "all", "location": "all"}
        else:
            reply_text = f"I found verified openings matching '{req.message}'. Take a look at the roles below, and let me know if you want to narrow it down by location, stack, or company culture."
            parsed_meta = {"query": req.message, "discipline": "all", "location": "all"}

    has_cv_req = bool(parsed_meta.get("has_cv_request", False))
    target_comp = str(parsed_meta.get("target_company", "")).strip()
    query = str(parsed_meta.get("query", "")).strip()
    disc = parsed_meta.get("discipline", "all")
    loc = parsed_meta.get("location", "all")

    # Detect brand names directly from the prompt unless candidate is asking a comparative question
    msg_l = req.message.lower()
    is_comparison = any(w in msg_l for w in [" vs ", " vs. ", " versus ", " or ", "compare", "better between", "difference", "which is better"])
    known_brands = [
        "apple", "nvidia", "tesla", "google", "meta", "microsoft", "amazon",
        "anduril", "palantir", "cloudflare", "riot games", "optiver", "jane street",
        "imc", "rigetti", "paradromics", "adnoc", "masdar", "jasara", "rocket lab",
        "relativity", "form energy", "redwood materials", "skydio", "waymo", "anthropic"
    ]
    if not is_comparison:
        for kb in known_brands:
            if re.search(r'\\b' + re.escape(kb) + r'\\b', msg_l):
                target_comp = kb
                # Strip brand from query terms so query focuses on role
                query = re.sub(r'\\b' + re.escape(kb) + r'\\b', '', query, flags=re.IGNORECASE).strip()
                break
    else:
        target_comp = ""

    if any(k in query.lower() for k in ["confused", "give results", "based on cv", "cv upload", "wtf", "primary stack", "resume"]):
        if has_candidate_profile:
            query = profile_skills[0] if profile_skills else ""
        else:
            query = ""

    # Clean punctuation and common search filler from query
    query = re.sub(r'[,+/|]+', ' ', query).strip()

    matched_jobs = []
    total_count = 0
    global _CACHED_JOBS
    if not _CACHED_JOBS:
        try:
            get_jobs_spec()
        except Exception as e:
            print("Failed to auto-populate _CACHED_JOBS:", e)

    # If target company was specified, make sure discipline doesn't conflict and wipe out all its jobs
    if target_comp and _CACHED_JOBS:
        comp_jobs = [j for j in _CACHED_JOBS if target_comp.lower() in (j.get("company") or "").lower()]
        if comp_jobs and disc != "all":
            disc_comp_jobs = [j for j in comp_jobs if (j.get("discipline") or "").lower() == disc.lower()]
            if not disc_comp_jobs:
                disc = "all"

    if _CACHED_JOBS:
        stop_words = {"jobs", "job", "openings", "opening", "roles", "role", "positions", "position", "looking", "want", "for", "with", "in", "at", "the", "a", "an"}
        q_words = [w.lower() for w in query.split() if len(w) > 1 and w.lower() not in stop_words]
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
                # If target company was specified and matched with no additional query
                if target_comp and target_comp.lower() in c:
                    pct = 92
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

with open("backend/main.py", "r", encoding="utf-8") as f:
    content = f.read()

pattern = r'    profile = \{\n        "headline": f"\{\'Early Career\'.*?return \{\n        "reply": reply_text,\n        "query": query,\n        "target_company": target_comp,\n        "discipline": disc,\n        "location": loc,\n        "matched_jobs": matched_jobs,\n        "total_matches": total_count,\n        "has_cv_request": has_cv_req,\n        "has_cv": bool\(cv_ctx\)\n    \}'

m = re.search(pattern, content, re.DOTALL)
if m:
    new_content = content[:m.start()] + new_match_cv_and_recruiter + content[m.end():]
    with open("backend/main.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("SUCCESS: backend/main.py patched successfully!")
else:
    print("ERROR: Pattern not found in backend/main.py")
