"""
Golden Eval Suite: Evaluates and iterates on Harvester & Janitor reasoning accuracy.
Measures:
1. Harvester schema extraction & talent pool filtering accuracy
2. Janitor 3-tier dead-link & soft-404 closure detection accuracy
"""

import os
import sys
import asyncio
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scrapers.job_janitor import JobJanitorAgent
from scrapers.job_harvester import JobHarvesterAgent

EVAL_CASES = [
    # --- JANITOR CLOSURE TESTS ---
    {
        "name": "Janitor: HTTP 404 dead link",
        "type": "janitor",
        "job": {
            "id": "mock-404",
            "title": "Quantum Systems Engineer",
            "company": "IonQ",
            "apply_url": "https://boards.greenhouse.io/ionq/jobs/999999999999_dead_link_test"
        },
        "expected_status": "closed"
    },
    {
        "name": "Janitor: Soft closure notice in page body",
        "type": "janitor_soft_closure",
        "title": "Senior AI Infrastructure Engineer",
        "company": "Frontier AI Lab",
        "snippet": "Thank you for your interest. This position has been filled and we are no longer accepting applications for this requisition. Please join our talent community for future updates.",
        "expected_closed": True
    },
    {
        "name": "Janitor: Active live job page snippet",
        "type": "janitor_soft_closure",
        "title": "Robotics Motion Planning Specialist",
        "company": "Skydio",
        "snippet": "About the role: Skydio is seeking an experienced Robotics Motion Planning engineer to build state-of-the-art autonomous flight algorithms. Apply below with your resume, portfolio, and work authorization.",
        "expected_closed": False
    },

    # --- HARVESTER ENRICHMENT TESTS ---
    {
        "name": "Harvester: Seniority & discipline reasoning",
        "type": "harvester_enrich",
        "raw_job": {
            "title": "Principal CUDA Acceleration Architect",
            "company": "Cerebras Systems",
            "ats_type": "greenhouse",
            "location": "Sunnyvale, CA (Hybrid / Remote)",
            "apply_url": "https://boards.greenhouse.io/cerebrassystems/jobs/123",
            "default_disc": "ai_ml"
        },
        "expected_min_exp": 6,
        "expected_disc": "ai_ml",
        "expected_skill": "CUDA"
    },
    {
        "name": "Harvester: Early career hardware extraction",
        "type": "harvester_enrich",
        "raw_job": {
            "title": "Junior FPGA Systems Test Engineer I",
            "company": "Tenstorrent",
            "ats_type": "greenhouse",
            "location": "Toronto, Canada",
            "apply_url": "https://boards.greenhouse.io/tenstorrent/jobs/456",
            "default_disc": "hardware"
        },
        "expected_min_exp": 0,
        "expected_disc": "hardware",
        "expected_skill": "FPGA"
    }
]

async def run_evals():
    print("=" * 65)
    print("CAMOUROLES AGENTIC REASONING EVALUATION SUITE")
    print("=" * 65)

    janitor = JobJanitorAgent(concurrency=5)
    harvester = JobHarvesterAgent()

    passed = 0
    total = len(EVAL_CASES)

    for case in EVAL_CASES:
        name = case["name"]
        ctype = case["type"]

        if ctype == "janitor":
            import httpx
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as probe_client:
                res = await janitor.verify_single_job(probe_client, case["job"])
                status = res["status"]
                is_pass = (status == case["expected_status"])
                print(f"[{'PASS' if is_pass else 'FAIL'}] {name} -> Got: {status} ({res['reason']})")
                if is_pass: passed += 1

        elif ctype == "janitor_soft_closure":
            is_closed = await janitor.ask_qwen_closure_reasoning(case["title"], case["company"], case["snippet"])
            is_pass = (is_closed == case["expected_closed"])
            print(f"[{'PASS' if is_pass else 'FAIL'}] {name} -> Qwen closed={is_closed} (Expected: {case['expected_closed']})")
            if is_pass: passed += 1

        elif ctype == "harvester_enrich":
            enriched_list = await harvester.reason_and_enrich_batch([case["raw_job"]])
            ej = enriched_list[0]
            min_exp_ok = ej["experience_min"] == case["expected_min_exp"]
            disc_ok = ej["discipline"] == case["expected_disc"]
            skill_ok = any(case["expected_skill"].lower() in s.lower() for s in ej["skills"])

            is_pass = min_exp_ok and disc_ok and skill_ok
            print(f"[{'PASS' if is_pass else 'FAIL'}] {name} -> MinExp: {ej['experience_min']}, Disc: {ej['discipline']}, Skills: {ej['skills']}")
            if is_pass: passed += 1

    print("=" * 65)
    score = (passed / total) * 100
    print(f"FINAL EVALUATION SCORE: {passed}/{total} PASSED ({score:.1f}%)")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_evals())
