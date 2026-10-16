import subprocess
import sys
import os
from datetime import datetime

def run_step(name, script_path):
    print(f"\n==================================================")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting: {name}")
    print(f"==================================================")
    res = subprocess.run([sys.executable, script_path], cwd=os.path.join(os.path.dirname(__file__), ".."))
    if res.returncode != 0:
        print(f"⚠ Warning: {name} exited with code {res.returncode}")
    else:
        print(f"[OK] {name} completed successfully.")

if __name__ == "__main__":
    print(f"=== camOroles Daily Update Pipeline (5:00 AM) ===")
    run_step("1. Y Combinator Job Scraper", "scrapers/ycombinator_scraper.py")
    run_step("2. Global 2,500 ATS Crawl", "scrapers/crawl_catalogue.py")
    run_step("3. Daily Liveness & Pruning Check", "scrapers/liveness.py")
    print(f"\n[OK] Pipeline finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
