"""
Camouroles Continuous 3-Hour Sync & Liveness Engine
Runs every 3 hours:
1. Ingests verified live roles from active Greenhouse boards & Y Combinator
2. Probes liveness of every single active job URL
3. Immediately deactivates and purges any 404/410/closed links
"""

import os
import sys
import time
import subprocess
from datetime import datetime, timezone

SYNC_INTERVAL_SECONDS = 3 * 60 * 60  # Exactly 3 hours (10,800 seconds)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_FILE = os.path.join(ROOT_DIR, "data", "cron_sync_3h.log")

def log(msg: str):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def run_step(name: str, script_relpath: str):
    script_path = os.path.join(ROOT_DIR, script_relpath)
    log(f"Starting: {name} ({script_relpath})")
    try:
        res = subprocess.run(
            [sys.executable, script_path],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=600  # 10 min max per step
        )
        if res.returncode == 0:
            log(f"[OK] {name} succeeded.")
        else:
            log(f"[WARN] {name} returned code {res.returncode}. Output:\n{res.stderr[-300:]}")
    except Exception as e:
        log(f"[ERROR] Running {name} failed: {e}")

def run_sync_cycle():
    log("=== STARTING 3-HOUR CATALOG SYNC & LIVENESS CYCLE ===")
    
    # Step 1: Autonomous Job Harvester Agent (Greenhouse, Lever, Ashby official boards)
    run_step("1. Job Harvester Agent (ATS Direct APIs)", "scrapers/job_harvester.py")
    
    # Step 2: Multi-Domain & Top Tech Brands
    run_step("2. Ingest Top Tech Brands (Apple, NVIDIA, Tesla)", "scrapers/ingest_top_brands.py")
    run_step("2b. Ingest Enterprise & Finance Roles", "scrapers/ingest_enterprise_multidomain.py")
    run_step("2c. Ingest Frontier & Deep-Tech Niches", "scrapers/ingest_frontier_niches.py")
    
    # Step 3: Ingest live Y Combinator startup roles
    run_step("3. Ingest Y Combinator Roles", "scrapers/ycombinator_scraper.py")
    
    # Step 4: Autonomous Job Janitor Agent (3-Tier Dead Link Pruning & Qwen Soft-404 Reasoning)
    run_step("4. Job Janitor Agent (Dead Link Pruning)", "scrapers/job_janitor.py")
    
    log("=== COMPLETED 3-HOUR SYNC & LIVENESS CYCLE ===")

def main():
    log(f"Camouroles 3-Hour Automation Daemon Initialized. Interval: {SYNC_INTERVAL_SECONDS}s")
    
    # Run first cycle immediately
    try:
        run_sync_cycle()
    except Exception as e:
        log(f"Error in initial sync cycle: {e}")
        
    while True:
        log(f"Sleeping for 3 hours until next cycle at {datetime.fromtimestamp(time.time() + SYNC_INTERVAL_SECONDS, tz=timezone.utc).strftime('%H:%M:%S UTC')}...")
        time.sleep(SYNC_INTERVAL_SECONDS)
        try:
            run_sync_cycle()
        except Exception as e:
            log(f"Error in recurring sync cycle: {e}")

if __name__ == "__main__":
    main()
