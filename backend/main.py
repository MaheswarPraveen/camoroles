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
    """Extracts and verifies Supabase JWT token from header, returning user_id."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")
    token = authorization.split(" ")[1]
    
    # Verify user with Supabase
    db = get_db()
    try:
        user_resp = db.auth.get_user(token)
        if not user_resp or not user_resp.user:
            raise HTTPException(status_code=401, detail="Invalid session token.")
        return user_resp.user.id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

# ---------- 1. Public Free Job Preview (No Login) ----------

@app.get("/api/jobs/preview")
def get_job_previews(limit: int = 15):
    """
    Public preview feed:
    Real active jobs from niche boards, but company name is masked and apply URL is withheld.
    """
    db = get_db()
    res = db.table("jobs").select("id, title, ats_type, location, is_remote, experience_min, experience_max, skills, last_verified_at, created_at")\
        .eq("is_active", True)\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    
    preview_items = []
    for j in res.data or []:
        # Masked company teasers
        ats = j.get("ats_type", "direct").capitalize()
        preview_items.append({
            "id": j["id"],
            "title": j["title"],
            "teaser_company": f"Stealth / {ats} Verified Employer",
            "location": j["location"],
            "is_remote": j["is_remote"],
            "experience": f"{j['experience_min']} - {j['experience_max']} yrs",
            "skills": j.get("skills", []),
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

# ---------- 3. User Matches Feed ----------

@app.get("/api/matches")
def get_user_matches(user_id: str = Depends(verify_token)):
    """
    Returns user's matches:
    - If status == 'unlocked' or user has active pass: reveals real company and apply URL.
    - Otherwise: company & apply_url are hidden.
    """
    db = get_db()
    
    # Check user entitlements
    ent_res = db.table("user_entitlements").select("*").eq("user_id", user_id).maybe_single().execute()
    ent = ent_res.data or {}
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
        "id, job_id, match_score, why_matched, status, created_at, jobs(title, company, apply_url, location, is_remote, experience_min, experience_max, skills)"
    ).eq("user_id", user_id).order("match_score", desc=True).execute()

    feed = []
    for m in res.data or []:
        job = m.get("jobs") or {}
        unlocked = is_unlimited or m["status"] == "unlocked"

        feed.append({
            "match_id": m["id"],
            "job_id": m["job_id"],
            "title": job.get("title", "Software Engineer"),
            "company": job.get("company", "Company") if unlocked else "Company (Unlock to view)",
            "apply_url": job.get("apply_url") if unlocked else None,
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

# ---------- 4. Unlock Apply Link ----------

@app.post("/api/matches/{job_id}/unlock")
def unlock_match(job_id: str, user_id: str = Depends(verify_token)):
    db = get_db()

    # Get entitlement
    ent_res = db.table("user_entitlements").select("*").eq("user_id", user_id).maybe_single().execute()
    ent = ent_res.data
    if not ent:
        db.table("user_entitlements").insert({"user_id": user_id, "free_unlocks_left": 3}).execute()
        ent = {"user_id": user_id, "free_unlocks_left": 3}

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
        # Decrement free unlock
        db.table("user_entitlements").update({"free_unlocks_left": free_left - 1}).eq("user_id", user_id).execute()

    # Mark match as unlocked
    db.table("job_matches").update({"status": "unlocked"}).eq("user_id", user_id).eq("job_id", job_id).execute()

    # Return the unlocked job details
    job_res = db.table("jobs").select("company, apply_url").eq("id", job_id).single().execute()
    return {
        "success": True,
        "company": job_res.data["company"],
        "apply_url": job_res.data["apply_url"],
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
