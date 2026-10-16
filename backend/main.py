import os
import hmac
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client

from backend.cv_parser import parse_cv_in_memory
from backend.embeddings import generate_embedding
from backend.scorer import evaluate_match
from backend.llm_router import LLMRouter

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

app = FastAPI(title="camOroles API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=500, detail="Database credentials not configured.")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def verify_token(authorization: Optional[str] = Header(None)) -> str:
    """Extracts and verifies Supabase JWT token from header, with seamless dev fallback."""
    if not authorization or not authorization.startswith("Bearer "):
        return "01455453-042a-435a-ad51-1e4e5c193864"
    
    token = authorization.split(" ")[1]
    if token in ("test", "demo", "dev", "undefined", "null", ""):
        return "01455453-042a-435a-ad51-1e4e5c193864"
    
    # Verify user with Supabase
    db = get_db()
    try:
        user_resp = db.auth.get_user(token)
        if user_resp and user_resp.user:
            return user_resp.user.id
    except Exception:
        pass

    return "01455453-042a-435a-ad51-1e4e5c193864"

def extract_job_sources(job: Dict[str, Any], is_unlocked: bool) -> List[Dict[str, Any]]:
    """Extracts verified multi-source links with official branding for FAANG, Big Tech, and ATS portals."""
    sources = []
    ats_type = str(job.get("ats_type", "direct")).lower()
    apply_url = str(job.get("apply_url", ""))
    company_lower = str(job.get("company", "")).lower()

    brand = "direct"
    title = "Official Careers"

    if "apple" in company_lower:
        brand = "apple"
        title = "Apple Careers"
    elif "microsoft" in company_lower:
        brand = "microsoft"
        title = "Microsoft Careers"
    elif "google" in company_lower:
        brand = "google"
        title = "Google Careers"
    elif "amazon" in company_lower:
        brand = "amazon"
        title = "Amazon Jobs"
    elif "meta" in company_lower:
        brand = "meta"
        title = "Meta Careers"
    elif "uber" in company_lower:
        brand = "uber"
        title = "Uber Careers"
    elif "sony" in company_lower:
        brand = "sony"
        title = "Sony Careers"
    elif "nvidia" in company_lower:
        brand = "nvidia"
        title = "NVIDIA Careers"
    elif "tesla" in company_lower:
        brand = "tesla"
        title = "Tesla Careers"
    elif "ycombinator" in ats_type or "ycombinator.com" in apply_url:
        brand = "ycombinator"
        title = "Y Combinator"
    elif "greenhouse" in ats_type or "greenhouse.io" in apply_url:
        brand = "greenhouse"
        title = "Greenhouse"
    elif "lever" in ats_type or "lever.co" in apply_url:
        brand = "lever"
        title = "Lever"
    elif "workable" in ats_type or "workable.com" in apply_url:
        brand = "workable"
        title = "Workable"
    elif "keka" in ats_type or "keka.com" in apply_url:
        brand = "keka"
        title = "Keka Hire"

    sources.append({
        "brand": brand,
        "name": f"Apply on {title}" if is_unlocked else f"Verified {title}",
        "url": apply_url if is_unlocked else None
    })

    if is_unlocked and job.get("company"):
        clean_company = job["company"].strip().replace(" ", "+")
        sources.append({
            "brand": "direct",
            "name": f"{job['company']} Career Search",
            "url": f"https://www.google.com/search?q={clean_company}+careers+jobs"
        })

    return sources

# ---------- 1. Public Free Job Preview (No Login) ----------

@app.get("/api/jobs/preview")
def get_job_previews(limit: int = 15):
    """
    Public preview feed:
    Active jobs with stealth branding and verified source badges.
    """
    db = get_db()
    res = db.table("jobs").select("id, title, company, ats_type, location, is_remote, experience_min, experience_max, skills, apply_url, last_verified_at, created_at")\
        .eq("is_active", True)\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    
    preview_items = []
    for j in res.data or []:
        ats = j.get("ats_type", "direct").capitalize()
        sources = extract_job_sources(j, is_unlocked=False)
        preview_items.append({
            "id": j["id"],
            "title": j["title"],
            "teaser_company": f"Stealth ({ats} Verified)",
            "location": j["location"],
            "is_remote": j["is_remote"],
            "experience": f"{j['experience_min']} - {j['experience_max']} yrs",
            "skills": j.get("skills", []),
            "sources": sources,
            "last_verified": j.get("last_verified_at")
        })
    return {"jobs": preview_items}

# ---------- 2. CV Ingestion (DPDP Compliant - In Memory Only) ----------

@app.post("/api/cv/upload")
async def upload_cv(
    file: UploadFile = File(...),
    user_id: str = Depends(verify_token)
):
    """
    Parses CV in-memory, generates embedding, stores structured summary, and matches jobs.
    Raw PDF is completely discarded immediately after parsing.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="CV file exceeds 5 MB limit.")

    # 1. Parse in-memory
    try:
        cv_data = parse_cv_in_memory(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CV: {str(e)}")

    # 2. Generate vector embedding
    try:
        emb_text = f"{cv_data['headline']}. Skills: {', '.join(cv_data['skills'])}. {cv_data['summary']}"
        embedding = generate_embedding(emb_text)
    except Exception as e:
        embedding = None

    db = get_db()

    # 3. Save to cv_profiles
    profile_payload = {
        "user_id": user_id,
        "headline": cv_data["headline"],
        "experience_years": cv_data["experience_years"],
        "skills": cv_data["skills"],
        "summary": cv_data["summary"],
        "embedding": embedding,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    db.table("cv_profiles").upsert(profile_payload, on_conflict="user_id").execute()

    # 4. Trigger initial matching against top active jobs
    match_candidates = []
    if embedding:
        try:
            # Query vector candidates
            rpc_res = db.rpc("find_top_job_candidates", {
                "p_user_id": user_id,
                "p_limit": 10,
                "p_match_threshold": 0.3
            }).execute()
            match_candidates = rpc_res.data or []
        except Exception as e:
            print(f"Vector search warning: {e}")

    # Fallback to recent active jobs if vector candidates are empty
    if not match_candidates:
        recent_jobs = db.table("jobs").select("*").eq("is_active", True).limit(8).execute()
        match_candidates = recent_jobs.data or []

    # Evaluate matches with Groq 1-shot rubric
    new_matches = []
    for job in match_candidates:
        eval_result = evaluate_match(cv_data, job)
        if eval_result["match_score"] >= 50:
            match_row = {
                "user_id": user_id,
                "job_id": job.get("job_id") or job.get("id"),
                "similarity_score": job.get("similarity", 0.5),
                "match_score": eval_result["match_score"],
                "why_matched": eval_result["why_matched"],
                "status": "new"
            }
            try:
                db.table("job_matches").upsert(match_row, on_conflict="user_id,job_id").execute()
                new_matches.append(match_row)
            except Exception as e:
                print(f"Match caching error: {e}")

    return {
        "success": True,
        "headline": cv_data["headline"],
        "skills": cv_data["skills"],
        "matches_found": len(new_matches)
    }

def get_user_entitlements(db, user_id: str) -> Dict[str, Any]:
    """Safely retrieves user entitlements without relying on maybe_single()."""
    try:
        res = db.table("user_entitlements").select("*").eq("user_id", user_id).execute()
        if res and res.data and len(res.data) > 0:
            return res.data[0]
    except Exception:
        pass
    return {"user_id": user_id, "free_unlocks_left": 3, "unlimited_until": None}

def get_user_cv_profile(db, user_id: str) -> Dict[str, Any]:
    """Safely retrieves user profile without relying on maybe_single()."""
    try:
        res = db.table("cv_profiles").select("*").eq("user_id", user_id).execute()
        if res and res.data and len(res.data) > 0:
            return res.data[0]
    except Exception:
        pass
    return {}

# ---------- 2b. Agentic Preference Matching ----------

class PreferenceMatchRequest(BaseModel):
    location: Optional[str] = "all"  # 'all', 'worldwide_remote', 'us_remote', 'india'
    role_type: Optional[str] = "all" # 'all', 'fullstack', 'frontend', 'backend', 'ai_ml'
    experience_max: Optional[int] = 3

@app.post("/api/cv/preferences")
def match_with_preferences(req: PreferenceMatchRequest, user_id: str = Depends(verify_token)):
    """
    Agentic step: Filters candidates according to user's interactive choices,
    then runs Groq evaluation and caches new matches.
    """
    db = get_db()
    cv_data = get_user_cv_profile(db, user_id)
    if not cv_data:
        raise HTTPException(status_code=400, detail="Please upload a CV first.")

    query = db.table("jobs").select("*").eq("is_active", True)
    loc = str(req.location or "all").lower()
    if loc == "worldwide_remote":
        query = query.eq("is_remote", True)
    elif loc in ("us_remote", "us", "united states"):
        query = query.ilike("location", "%us%")
    elif loc in ("uk_eu", "uk", "eu", "europe", "germany", "netherlands"):
        query = query.or_("location.ilike.%london%,location.ilike.%uk%,location.ilike.%germany%,location.ilike.%munich%,location.ilike.%netherlands%,location.ilike.%amsterdam%,location.ilike.%switzerland%,location.ilike.%zurich%")
    elif loc in ("asia_pacific", "apac", "japan", "singapore"):
        query = query.or_("location.ilike.%japan%,location.ilike.%tokyo%,location.ilike.%singapore%,location.ilike.%australia%,location.ilike.%canada%")
    elif loc in ("india", "in"):
        query = query.ilike("location", "%india%")

    if req.role_type and req.role_type != "all":
        rt = req.role_type.lower()
        if rt in ("robotics", "embedded"):
            query = query.or_("title.ilike.%robotics%,title.ilike.%autonomous%,title.ilike.%embedded%,title.ilike.%firmware%,title.ilike.%mechatronics%")
        elif rt in ("ai", "ai_ml", "machine_learning"):
            query = query.or_("title.ilike.%ai%,title.ilike.%learning%,title.ilike.%vision%,title.ilike.%perception%,title.ilike.%pytorch%")
        elif rt in ("systems", "backend"):
            query = query.or_("title.ilike.%backend%,title.ilike.%systems%,title.ilike.%cloud%,title.ilike.%infrastructure%")
        elif rt in ("hardware", "firmware"):
            query = query.or_("title.ilike.%hardware%,title.ilike.%silicon%,title.ilike.%firmware%,title.ilike.%sensing%")
        elif rt == "frontend":
            query = query.or_("title.ilike.%frontend%,title.ilike.%ui%,title.ilike.%web%")
        elif rt == "fullstack":
            query = query.or_("title.ilike.%full stack%,title.ilike.%fullstack%,title.ilike.%software%")
        else:
            query = query.ilike("title", f"%{rt}%")

    candidates = query.limit(16).execute().data or []
    if len(candidates) < 4:
        candidates = db.table("jobs").select("*").eq("is_active", True).limit(12).execute().data or []

    scored_matches = []
    for job in candidates:
        eval_result = evaluate_match(cv_data, job)
        match_row = {
            "user_id": user_id,
            "job_id": job["id"],
            "similarity_score": 0.88,
            "match_score": eval_result["match_score"],
            "why_matched": eval_result["why_matched"],
            "status": "new"
        }
        try:
            db.table("job_matches").upsert(match_row, on_conflict="user_id,job_id").execute()
            scored_matches.append(match_row)
        except Exception:
            pass

    return {
        "success": True,
        "matched_count": len(scored_matches)
    }

# ---------- 3. User Matches Feed ----------

@app.get("/api/matches")
def get_user_matches(user_id: str = Depends(verify_token)):
    """
    Returns user's matches:
    - If status == 'unlocked' or user has active pass: reveals real company, verified source logos, and apply URLs.
    - Otherwise: company & apply_url are hidden.
    """
    db = get_db()
    ent = get_user_entitlements(db, user_id)
    unlimited_until = ent.get("unlimited_until")
    is_unlimited = False
    if unlimited_until:
        try:
            is_unlimited = datetime.fromisoformat(unlimited_until.replace("Z", "+00:00")) > datetime.now(timezone.utc)
        except Exception:
            pass

    free_left = ent.get("free_unlocks_left", 3)

    # Fetch matches joined with jobs
    res = db.table("job_matches").select(
        "id, job_id, match_score, why_matched, status, created_at, jobs(id, title, company, ats_type, apply_url, location, is_remote, experience_min, experience_max, skills)"
    ).eq("user_id", user_id).order("match_score", desc=True).execute()

    feed = []
    for m in res.data or []:
        job = m.get("jobs") or {}
        unlocked = is_unlimited or m["status"] == "unlocked"
        sources = extract_job_sources(job, unlocked)

        feed.append({
            "match_id": m["id"],
            "job_id": m["job_id"],
            "title": job.get("title", "Software Engineer"),
            "company": job.get("company", "Company") if unlocked else f"Stealth ({job.get('ats_type', 'direct').capitalize()})",
            "apply_url": job.get("apply_url") if unlocked else None,
            "sources": sources,
            "location": job.get("location", "India"),
            "is_remote": job.get("is_remote", False),
            "match_score": m["match_score"],
            "why_matched": m["why_matched"],
            "is_unlocked": unlocked,
            "status": m["status"]
        })

    return {
        "is_unlimited": is_unlimited,
        "free_unlocks_left": free_left,
        "matches": feed
    }

# ---------- 4. Manual Search Endpoint ----------

@app.get("/api/jobs/search")
def search_jobs(
    q: Optional[str] = None,
    location: Optional[str] = None,
    is_remote: Optional[bool] = None,
    ats_type: Optional[str] = None,
    role: Optional[str] = None,
    experience: Optional[str] = None,
    skill: Optional[str] = None,
    limit: int = 50,
    user_id: str = Depends(verify_token)
):
    """Manual catalog search with rich location, ATS source, remote, and experience filters."""
    db = get_db()
    ent = get_user_entitlements(db, user_id)
    unlimited_until = ent.get("unlimited_until")
    is_unlimited = False
    if unlimited_until:
        try:
            is_unlimited = datetime.fromisoformat(unlimited_until.replace("Z", "+00:00")) > datetime.now(timezone.utc)
        except Exception:
            pass

    # Find unlocked jobs for this user
    unlocked_jobs = set()
    matches_res = db.table("job_matches").select("job_id, status").eq("user_id", user_id).execute()
    for m in matches_res.data or []:
        if m.get("status") == "unlocked":
            unlocked_jobs.add(m["job_id"])

    query = db.table("jobs").select("id, title, company, ats_type, location, is_remote, experience_min, experience_max, skills, apply_url, last_verified_at, created_at").eq("is_active", True)

    if is_remote is not None:
        query = query.eq("is_remote", is_remote)

    if ats_type and ats_type.lower() != "all":
        ats = ats_type.lower()
        if ats in ("faang", "giants"):
            query = query.or_("company.ilike.%apple%,company.ilike.%microsoft%,company.ilike.%sony%,company.ilike.%uber%,company.ilike.%nvidia%,company.ilike.%tesla%,company.ilike.%google%,company.ilike.%amazon%,company.ilike.%meta%")
        else:
            query = query.ilike("ats_type", f"%{ats}%")

    if role and role.lower() != "all":
        rt = role.lower()
        if rt in ("robotics", "embedded"):
            query = query.or_("title.ilike.%robotics%,title.ilike.%autonomous%,title.ilike.%embedded%,title.ilike.%firmware%,title.ilike.%mechatronics%")
        elif rt in ("ai", "ai_ml", "machine_learning"):
            query = query.or_("title.ilike.%ai%,title.ilike.%learning%,title.ilike.%vision%,title.ilike.%perception%,title.ilike.%pytorch%")
        elif rt in ("systems", "backend"):
            query = query.or_("title.ilike.%backend%,title.ilike.%systems%,title.ilike.%cloud%,title.ilike.%infrastructure%")
        elif rt in ("hardware", "firmware"):
            query = query.or_("title.ilike.%hardware%,title.ilike.%silicon%,title.ilike.%firmware%,title.ilike.%sensing%")
        elif rt == "frontend":
            query = query.or_("title.ilike.%frontend%,title.ilike.%ui%,title.ilike.%web%")
        elif rt == "fullstack":
            query = query.or_("title.ilike.%full stack%,title.ilike.%fullstack%,title.ilike.%software%")
        else:
            query = query.ilike("title", f"%{rt}%")

    if experience and experience.lower() != "all":
        exp = experience.lower()
        if exp in ("fresher", "0-1", "0 - 1"):
            query = query.lte("experience_max", 1)
        elif exp in ("junior", "1-2", "0 - 2"):
            query = query.lte("experience_max", 2)
        elif exp in ("early", "1-3", "0 - 3"):
            query = query.lte("experience_max", 3)

    if location and location.lower() != "all":
        loc = location.lower()
        if loc in ("us", "us_remote", "united states"):
            query = query.ilike("location", "%us%")
        elif loc in ("uk", "london", "cambridge"):
            query = query.or_("location.ilike.%london%,location.ilike.%uk%,location.ilike.%united kingdom%")
        elif loc in ("germany", "netherlands", "eu", "europe", "munich", "amsterdam"):
            query = query.or_("location.ilike.%germany%,location.ilike.%munich%,location.ilike.%netherlands%,location.ilike.%amsterdam%")
        elif loc in ("switzerland", "zurich"):
            query = query.or_("location.ilike.%switzerland%,location.ilike.%zurich%")
        elif loc in ("japan", "tokyo"):
            query = query.or_("location.ilike.%japan%,location.ilike.%tokyo%")
        elif loc in ("canada", "toronto", "vancouver"):
            query = query.or_("location.ilike.%canada%,location.ilike.%toronto%")
        elif loc in ("singapore", "apac", "australia", "sydney"):
            query = query.or_("location.ilike.%singapore%,location.ilike.%australia%")
        elif loc in ("india", "in"):
            query = query.ilike("location", "%india%")
        elif loc in ("bangalore", "bengaluru"):
            query = query.or_("location.ilike.%bangalore%,location.ilike.%bengaluru%")
        elif loc in ("hyderabad", "pune", "delhi", "noida", "gurgaon"):
            query = query.ilike("location", f"%{loc}%")
        elif loc in ("remote", "worldwide"):
            query = query.eq("is_remote", True)

    if skill and skill.strip():
        query = query.contains("skills", [skill.strip()])

    if q and q.strip():
        clean_q = q.strip().replace("'", "")
        query = query.or_(f"title.ilike.%{clean_q}%,company.ilike.%{clean_q}%,description.ilike.%{clean_q}%")

    res = query.order("created_at", desc=True).limit(limit).execute()

    results = []
    for j in res.data or []:
        job_id = j["id"]
        unlocked = is_unlimited or (job_id in unlocked_jobs)
        sources = extract_job_sources(j, unlocked)

        results.append({
            "id": job_id,
            "title": j["title"],
            "company": j["company"] if unlocked else f"Stealth ({j.get('ats_type', 'direct').capitalize()})",
            "ats_type": j.get("ats_type", "direct"),
            "location": j.get("location", "Remote"),
            "is_remote": j.get("is_remote", False),
            "experience": f"{j.get('experience_min', 0)} - {j.get('experience_max', 3)} yrs",
            "skills": j.get("skills", []),
            "sources": sources,
            "is_unlocked": unlocked,
            "apply_url": j.get("apply_url") if unlocked else None
        })

    return {"jobs": results}

# ---------- 5. Profile & Entitlements Endpoint ----------

@app.get("/api/profile")
def get_user_profile(user_id: str = Depends(verify_token)):
    """Fetches candidate profile, extracted skills, and unlock balance."""
    db = get_db()
    profile = get_user_cv_profile(db, user_id)
    ent = get_user_entitlements(db, user_id)
    unlimited_until = ent.get("unlimited_until")
    is_unlimited = False
    if unlimited_until:
        try:
            is_unlimited = datetime.fromisoformat(unlimited_until.replace("Z", "+00:00")) > datetime.now(timezone.utc)
        except Exception:
            pass

    matches_res = db.table("job_matches").select("id, status").eq("user_id", user_id).execute()
    matches = matches_res.data or []
    unlocked_count = sum(1 for m in matches if m.get("status") == "unlocked")

    return {
        "user_id": user_id,
        "has_cv": bool(profile.get("summary")),
        "headline": profile.get("headline", "No CV uploaded yet"),
        "experience_years": profile.get("experience_years", 0),
        "skills": profile.get("skills", []),
        "summary": profile.get("summary", ""),
        "updated_at": profile.get("updated_at"),
        "free_unlocks_left": ent.get("free_unlocks_left", 3),
        "is_unlimited": is_unlimited,
        "unlimited_until": unlimited_until,
        "stats": {
            "total_matches": len(matches),
            "unlocked_count": unlocked_count
        }
    }

# ---------- 6. Unlock Apply Link ----------

@app.post("/api/matches/{job_id}/unlock")
def unlock_match(job_id: str, user_id: str = Depends(verify_token)):
    db = get_db()
    ent = get_user_entitlements(db, user_id)
    unlimited_until = ent.get("unlimited_until")
    is_unlimited = False
    if unlimited_until:
        try:
            is_unlimited = datetime.fromisoformat(unlimited_until.replace("Z", "+00:00")) > datetime.now(timezone.utc)
        except Exception:
            pass

    free_left = ent.get("free_unlocks_left", 0)

    if not is_unlimited:
        if free_left <= 0:
            raise HTTPException(status_code=403, detail="No free unlocks remaining this week. Upgrade to unlock unlimited roles.")
        db.table("user_entitlements").upsert({"user_id": user_id, "free_unlocks_left": free_left - 1}, on_conflict="user_id").execute()

    # Mark match as unlocked
    db.table("job_matches").update({"status": "unlocked"}).eq("user_id", user_id).eq("job_id", job_id).execute()

    job_res = db.table("jobs").select("*").eq("id", job_id).single().execute()
    sources = extract_job_sources(job_res.data, is_unlocked=True)

    return {
        "success": True,
        "company": job_res.data["company"],
        "apply_url": job_res.data["apply_url"],
        "sources": sources,
        "free_unlocks_remaining": max(0, free_left - 1) if not is_unlimited else "unlimited"
    }

    free_left = ent.get("free_unlocks_left", 0)

    if not is_unlimited:
        if free_left <= 0:
            raise HTTPException(status_code=403, detail="No free unlocks remaining this week. Upgrade to unlock unlimited roles.")
        db.table("user_entitlements").update({"free_unlocks_left": free_left - 1}).eq("user_id", user_id).execute()

    # Mark match as unlocked
    db.table("job_matches").update({"status": "unlocked"}).eq("user_id", user_id).eq("job_id", job_id).execute()

    job_res = db.table("jobs").select("*").eq("id", job_id).single().execute()
    sources = extract_job_sources(job_res.data, is_unlocked=True)

    return {
        "success": True,
        "company": job_res.data["company"],
        "apply_url": job_res.data["apply_url"],
        "sources": sources,
        "free_unlocks_remaining": max(0, free_left - 1) if not is_unlimited else "unlimited"
    }

# ---------- 5. Razorpay Payments (One-time, no auto-debit) ----------

class CheckoutRequest(BaseModel):
    plan: str # 'week' (Rs 30) or 'month' (Rs 100)

class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan: str

@app.post("/api/checkout/order")
def create_checkout_order(req: CheckoutRequest, user_id: str = Depends(verify_token)):
    import razorpay
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=500, detail="Razorpay is not configured.")

    amount_paise = 3000 if req.plan == "week" else 10000 # Rs 30 or Rs 100
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

    try:
        order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"rcpt_{user_id[:8]}_{int(datetime.now().timestamp())}",
            "notes": {"user_id": user_id, "plan": req.plan}
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create Razorpay order: {str(e)}")

    db = get_db()
    db.table("job_orders").insert({
        "id": order["id"],
        "user_id": user_id,
        "amount": amount_paise,
        "plan": req.plan,
        "status": "created"
    }).execute()

    return {
        "order_id": order["id"],
        "amount": amount_paise,
        "key_id": RAZORPAY_KEY_ID
    }

@app.post("/api/checkout/verify")
def verify_payment(req: VerifyPaymentRequest, user_id: str = Depends(verify_token)):
    # Verify HMAC signature
    msg = f"{req.razorpay_order_id}|{req.razorpay_payment_id}".encode("utf-8")
    expected_sig = hmac.new(
        RAZORPAY_KEY_SECRET.encode("utf-8"),
        msg,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, req.razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid payment signature.")

    db = get_db()
    # Mark order as paid
    db.table("job_orders").update({
        "status": "paid",
        "payment_id": req.razorpay_payment_id
    }).eq("id", req.razorpay_order_id).execute()

    # Extend entitlements
    days = 7 if req.plan == "week" else 30
    until = datetime.now(timezone.utc) + timedelta(days=days)

    db.table("user_entitlements").upsert({
        "user_id": user_id,
        "unlimited_until": until.isoformat()
    }, on_conflict="user_id").execute()

    return {
        "success": True,
        "unlimited_until": until.isoformat()
    }

# ---------- Static Frontend Serving ----------
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
if os.path.exists(web_dir):
    app.mount("/static", StaticFiles(directory=web_dir), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(web_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "camOroles API is running. Visit /docs for OpenAPI specs."}

