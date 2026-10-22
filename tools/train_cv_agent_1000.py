"""
CAMOUROLES CV READING AGENT - 1,000 ITERATION HIGH-PERFORMANCE REWARD-BASED POLICY TRAINING
==========================================================================================
Vectorized feature pre-computation for 10,000+ jobs. Executes 1,000 optimization iterations
in ~5 to 8 seconds with full progress streaming and comprehensive report generation.
"""

import os
import sys
import json
import math
import random
import time
import re
from typing import Dict, List, Any, Tuple

# Enable unbuffered line streaming
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

BENCHMARK_PROFILES = [
    {
        "id": "cand-01-junior-robotics",
        "headline": "Robotics and AI Research Engineer",
        "experienceYears": 1,
        "skills": ["Python", "C/C++", "ROS 2", "ArduPilot", "PyTorch", "OpenCV"],
        "discipline": "robotics",
        "is_tech": True
    },
    {
        "id": "cand-02-senior-kernel",
        "headline": "Senior Staff Distributed Systems & Kernel Engineer",
        "experienceYears": 8,
        "skills": ["Rust", "C++", "Linux Kernel", "DPDK", "eBPF", "Distributed Systems"],
        "discipline": "backend",
        "is_tech": True
    },
    {
        "id": "cand-03-junior-safety",
        "headline": "Junior Fire & Life Safety Engineer",
        "experienceYears": 1.5,
        "skills": ["Fire Protection", "AutoCAD", "NFPA", "Life Safety Code", "Smoke Evacuation"],
        "discipline": "safety",
        "is_tech": True
    },
    {
        "id": "cand-04-mid-frontend",
        "headline": "Frontend UI/UX Systems Engineer",
        "experienceYears": 3.5,
        "skills": ["React", "TypeScript", "Next.js", "Tailwind CSS", "Web Vitals", "GraphQL"],
        "discipline": "frontend",
        "is_tech": True
    },
    {
        "id": "cand-05-senior-hft",
        "headline": "Ultra-Low-Latency HFT C++ Systems Lead",
        "experienceYears": 7,
        "skills": ["Modern C++", "Low Latency", "FPGA", "Network Bypass", "Order Book", "Market Making"],
        "discipline": "trading",
        "is_tech": True
    },
    {
        "id": "cand-06-legal-paralegal",
        "headline": "Senior Corporate Paralegal & Contract Compliance Specialist",
        "experienceYears": 6,
        "skills": ["Contract Management", "Corporate Governance", "NDA Review", "Regulatory Compliance"],
        "discipline": "legal",
        "is_tech": False
    },
    {
        "id": "cand-07-mid-hardware",
        "headline": "ASIC / FPGA Digital RTL Design Engineer",
        "experienceYears": 4,
        "skills": ["SystemVerilog", "RTL", "UVM", "FPGA", "Synthesis", "Timing Closure"],
        "discipline": "hardware",
        "is_tech": True
    },
    {
        "id": "cand-08-newgrad-ml",
        "headline": "Junior Computer Vision / ML Research Associate",
        "experienceYears": 0.5,
        "skills": ["PyTorch", "TensorFlow", "Computer Vision", "Python", "Transformers"],
        "discipline": "ai",
        "is_tech": True
    }
]

DISCIPLINE_PATTERNS = {
    'robotics': re.compile(r'\b(robot|robotics|autonomy|autonomous|uav|drone|ros|ros2|slam|ardupilot|px4|mechatronics|kinematics|perception|motion planning|controls)\b', re.I),
    'frontend': re.compile(r'\b(frontend|front[- ]end|react|vue|angular|svelte|web developer|javascript|typescript|ui|ux)\b', re.I),
    'backend': re.compile(r'\b(backend|back[- ]end|golang|rust|distributed systems|microservices|cloud|server|database|infra|kernel)\b', re.I),
    'ai': re.compile(r'\b(ai|artificial intelligence|machine learning|deep learning|llm|computer vision|nlp|neural|genai)\b', re.I),
    'trading': re.compile(r'\b(trading|quant|hft|low latency|market making|order book)\b', re.I),
    'hardware': re.compile(r'\b(hardware|asic|fpga|silicon|rtl|soc|risc-v|semiconductor|vlsi)\b', re.I),
    'safety': re.compile(r'\b(safety|fire|ehs|hazard|process safety|systems safety|flight safety|system safety|mission assurance|reliability)\b', re.I),
    'legal': re.compile(r'\b(paralegal|legal|compliance|counsel|contracts|regulatory|attorney)\b', re.I),
}

NON_TECH_RX = re.compile(r'\b(paralegal|legal|counsel|attorney|lawyer|compliance|recruiter|recruiting|talent|sourcer|human resources|hr|accountant|accounting|bookkeeper|payroll|controller|treasury|finance|sales|marketing|account executive|business development|retail)\b', re.I)
TECH_SWE_RX = re.compile(r'\b(software engineer|backend|frontend|fullstack|firmware|devops|sre|machine learning|ml engineer|deep learning|data engineer|cloud engineer|kernel|fpga|asic|embedded engineer|systems engineer|autonomy engineer|robotics engineer)\b', re.I)
SENIOR_TIER_RX = re.compile(r'\b(senior|staff|lead|principal|director|head of|vp|manager|architect|chief)\b', re.I)
JUNIOR_TIER_RX = re.compile(r'\b(junior|associate|entry|graduate|intern|trainee|analyst|level 1|level i\b|swe i\b|engineer i\b)\b', re.I)

def load_catalog_jobs():
    import httpx
    try:
        r = httpx.get('https://camouroles.primemax.workers.dev/api/jobs', timeout=20.0)
        jobs = r.json().get('jobs', [])
        print(f"[DATASET] Loaded {len(jobs)} active jobs from Edge Catalog.")
        return jobs
    except Exception as e:
        print(f"[DATASET] Error loading jobs: {e}")
        return []

def precompute_job_features(candidates: List[Dict[str, Any]], jobs: List[Dict[str, Any]]):
    """
    Pre-computes boolean and integer features for all candidate-job pairs.
    Transforms 81 million regex evaluations into ultra-fast array lookups.
    """
    t0 = time.time()
    print("[PRE-COMPUTING] Indexing candidate-job feature matrices...")
    
    # Pre-parse job traits
    parsed_jobs = []
    for j in jobs:
        t = (j.get("title") or "").strip()
        t_lower = t.lower()
        j_disc = (j.get("discipline") or "").lower()
        j_skills = [str(s).lower() for s in (j.get("skills") or [])]
        min_exp = j.get("minExp") or 0
        max_exp = j.get("maxExp") or 10

        is_non_tech = bool(NON_TECH_RX.search(t_lower))
        is_tech_swe = bool(TECH_SWE_RX.search(t_lower))
        is_senior = bool(SENIOR_TIER_RX.search(t_lower)) or min_exp >= 5
        is_junior = bool(JUNIOR_TIER_RX.search(t_lower)) or (min_exp <= 2 and not is_senior)

        parsed_jobs.append({
            "id": j.get("id"),
            "title": t,
            "company": j.get("company", ""),
            "discipline": j_disc,
            "min_exp": min_exp,
            "max_exp": max_exp,
            "is_non_tech": is_non_tech,
            "is_tech_swe": is_tech_swe,
            "is_senior": is_senior,
            "is_junior": is_junior,
            "t_lower": t_lower,
            "j_skills": j_skills
        })

    # Pre-compute candidate-specific job traits
    cand_matrices = []
    for cand in candidates:
        cand_disc = cand["discipline"]
        cand_exp = cand["experienceYears"]
        cand_is_tech = cand["is_tech"]
        cand_skills = [s.lower() for s in cand["skills"]]
        disc_rx = DISCIPLINE_PATTERNS.get(cand_disc)

        cand_job_features = []
        for pj in parsed_jobs:
            # Disqualification
            if cand_is_tech and pj["is_non_tech"]:
                continue
            if (not cand_is_tech) and pj["is_tech_swe"]:
                continue

            # Domain match
            is_direct_disc = (pj["discipline"] == cand_disc or (disc_rx and disc_rx.search(pj["t_lower"])))
            is_adj_disc = False
            if cand_disc == "robotics" and (pj["discipline"] in ["ai", "hardware"] or any(k in pj["t_lower"] for k in ["computer vision", "perception", "controls", "firmware"])):
                is_adj_disc = True
            elif cand_disc == "ai" and (pj["discipline"] in ["backend", "robotics"] or any(k in pj["t_lower"] for k in ["data engineer", "gpu", "distributed systems"])):
                is_adj_disc = True

            # Title match
            title_hit = bool(disc_rx and disc_rx.search(pj["t_lower"]))

            # Skills overlap
            skill_hits = 0
            for cs in cand_skills:
                if any(cs in js or js in cs for js in pj["j_skills"]) or cs in pj["t_lower"]:
                    skill_hits += 1

            cand_job_features.append({
                "job_id": pj["id"],
                "title": pj["title"],
                "company": pj["company"],
                "is_direct_disc": is_direct_disc,
                "is_adj_disc": is_adj_disc,
                "title_hit": title_hit,
                "skill_hits": skill_hits,
                "is_senior": pj["is_senior"],
                "is_junior": pj["is_junior"],
                "min_exp": pj["min_exp"],
                "max_exp": pj["max_exp"]
            })

        cand_matrices.append({
            "candidate": cand,
            "features": cand_job_features
        })

    print(f"[PRE-COMPUTING] Done in {time.time() - t0:.2f}s. Ready for high-speed simulation.")
    return cand_matrices

def fast_eval_policy(cand_data: Dict[str, Any], weights: Dict[str, float]) -> Tuple[float, Dict[str, Any]]:
    cand = cand_data["candidate"]
    cand_exp = cand["experienceYears"]
    features = cand_data["features"]

    w_disc_direct = weights["w_disc_direct"]
    w_disc_adj = weights["w_disc_adjacent"]
    w_title = weights["w_title_direct"]
    w_skills_max = weights["w_skills_max"]
    w_skills_hit = weights["w_skills_per_hit"]
    pen_senior = weights["pen_senior_on_junior"]
    rew_junior = weights["rew_junior_boost"]
    rew_mid = weights["rew_mid_align"]
    rew_senior = weights["rew_senior_boost"]
    pen_junior = weights["pen_junior_on_senior"]

    scored = []

    for f in features:
        score = 0.0
        if f["is_direct_disc"]:
            score += w_disc_direct
        elif f["is_adj_disc"]:
            score += w_disc_adj

        if f["title_hit"]:
            score += w_title

        score += min(w_skills_max, f["skill_hits"] * w_skills_hit)

        is_sr = f["is_senior"]
        is_jr = f["is_junior"]

        if cand_exp <= 2:
            if is_sr:
                score -= pen_senior
            elif is_jr:
                score += rew_junior
            elif f["min_exp"] <= 2:
                score += rew_mid
        elif cand_exp >= 6:
            if is_sr:
                score += rew_senior
            elif is_jr:
                score -= pen_junior
        else:
            if cand_exp >= f["min_exp"] and cand_exp <= f["max_exp"]:
                score += rew_mid

        if score >= 45.0:
            final_score = min(96.0, max(50.0, score))
            scored.append((final_score, f))

    if not scored:
        return -50.0, {"top_count": 0, "domain_acc": 0, "seniority_acc": 0}

    scored.sort(key=lambda x: -x[0])
    top_50 = scored[:50]

    domain_hits = sum(1 for s, f in top_50 if f["is_direct_disc"])
    domain_precision = domain_hits / len(top_50)

    if cand_exp <= 2:
        seniority_clean = sum(1 for s, f in top_50 if not f["is_senior"])
        seniority_precision = seniority_clean / len(top_50)
    elif cand_exp >= 6:
        seniority_clean = sum(1 for s, f in top_50 if f["is_senior"])
        seniority_precision = seniority_clean / len(top_50)
    else:
        seniority_precision = 1.0

    reward = (domain_precision * 45.0) + (seniority_precision * 40.0) + (min(1.0, len(top_50) / 50.0) * 15.0)

    return reward, {
        "top_count": len(top_50),
        "domain_acc": domain_precision,
        "seniority_acc": seniority_precision,
        "top_1_score": top_50[0][0],
        "top_1_title": top_50[0][1]["title"],
        "top_1_company": top_50[0][1]["company"]
    }

def run_training_1000():
    jobs = load_catalog_jobs()
    if not jobs:
        print("Cannot run without jobs.")
        return

    cand_matrices = precompute_job_features(BENCHMARK_PROFILES, jobs)

    print("=" * 75)
    print("CAMOUROLES CV AGENT - 1,000 ITERATION REWARD-BASED POLICY TRAINING")
    print("=" * 75)

    weights = {
        "w_disc_direct": 35.0,
        "w_disc_adjacent": 18.0,
        "w_title_direct": 25.0,
        "w_skills_max": 25.0,
        "w_skills_per_hit": 8.0,
        "pen_senior_on_junior": 40.0,
        "rew_junior_boost": 25.0,
        "rew_mid_align": 15.0,
        "rew_senior_boost": 20.0,
        "pen_junior_on_senior": 30.0
    }

    best_weights = weights.copy()
    
    # Calculate initial baseline
    baseline_rewards = [fast_eval_policy(cm, weights)[0] for cm in cand_matrices]
    baseline_avg = sum(baseline_rewards) / len(baseline_rewards)
    best_avg_reward = baseline_avg
    print(f"[BASELINE] Step 0 Initial Reward: {baseline_avg:.2f} / 100.00\n")

    history = []
    t_start = time.time()

    temperature = 1.0
    min_temp = 0.05
    decay = 0.996

    for step in range(1, 1001):
        # Perturb one weight
        param = random.choice(list(weights.keys()))
        delta = random.choice([-2.0, -1.0, -0.5, 0.5, 1.0, 2.0]) * temperature

        test_weights = weights.copy()
        test_weights[param] = max(5.0, min(65.0, test_weights[param] + delta))

        # Evaluate across cohort
        rewards = []
        domain_accs = []
        seniority_accs = []
        for cm in cand_matrices:
            r, meta = fast_eval_policy(cm, test_weights)
            rewards.append(r)
            domain_accs.append(meta["domain_acc"])
            seniority_accs.append(meta["seniority_acc"])

        avg_r = sum(rewards) / len(rewards)
        mean_domain = sum(domain_accs) / len(domain_accs)
        mean_seniority = sum(seniority_accs) / len(seniority_accs)

        diff = avg_r - baseline_avg
        if diff > 0 or random.random() < math.exp(max(-10.0, diff / max(0.01, temperature))):
            weights = test_weights
            baseline_avg = avg_r
            if avg_r > best_avg_reward:
                best_avg_reward = avg_r
                best_weights = weights.copy()

        temperature = max(min_temp, temperature * decay)

        if step % 100 == 0 or step == 1000:
            elapsed = time.time() - t_start
            history.append({
                "step": step,
                "reward": baseline_avg,
                "domain_accuracy": mean_domain,
                "seniority_accuracy": mean_seniority,
                "temperature": temperature,
                "elapsed_sec": round(elapsed, 2)
            })
            print(f"Step {step:4d}/1000 | Reward: {baseline_avg:6.2f} | Domain Acc: {mean_domain*100:5.1f}% | Seniority Acc: {mean_seniority*100:5.1f}% | Elapsed: {elapsed:4.1f}s")

    total_time = time.time() - t_start
    print("\n" + "=" * 75)
    print(f"TRAINING CONVERGED IN {total_time:.2f}s! Best Average Reward: {best_avg_reward:.2f} / 100.00")
    print("=" * 75)

    print("\n[OPTIMAL CONVERGED WEIGHT POLICY]:")
    for k, v in best_weights.items():
        print(f"  {k:22s}: {v:.1f}")

    print("\n[EVALUATION REPORT ACROSS BENCHMARK PROFILES]:")
    report_rows = []
    for cm in cand_matrices:
        r, meta = fast_eval_policy(cm, best_weights)
        c = cm["candidate"]
        report_rows.append({
            "candidate": c["headline"],
            "yoe": c["experienceYears"],
            "discipline": c["discipline"],
            "reward": r,
            "domain_acc": meta["domain_acc"],
            "seniority_acc": meta["seniority_acc"],
            "top1_title": meta["top_1_title"],
            "top1_company": meta["top_1_company"],
            "top1_score": meta["top_1_score"]
        })
        print(f"\n{c['headline']} ({c['experienceYears']} YOE, {c['discipline'].upper()}):")
        print(f"  Reward Score:       {r:.2f} / 100")
        print(f"  Domain Accuracy:    {meta['domain_acc']*100:.1f}%")
        print(f"  Seniority Accuracy: {meta['seniority_acc']*100:.1f}%")
        print(f"  Top Match #1:       {meta['top_1_title']} @ {meta['top_1_company']} ({meta['top_1_score']}%)")

    # Save artifact
    os.makedirs("data", exist_ok=True)
    report_path = "data/cv_agent_1000_eval_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "iterations": 1000,
            "total_time_seconds": round(total_time, 2),
            "baseline_avg_reward": round(sum(baseline_rewards)/len(baseline_rewards), 2),
            "best_avg_reward": round(best_avg_reward, 2),
            "weights": best_weights,
            "convergence_history": history,
            "profile_results": report_rows
        }, f, indent=2)
    print(f"\n[REPORT] Saved full evaluation report to {report_path}")

if __name__ == "__main__":
    run_training_1000()
