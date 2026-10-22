import httpx
import re
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

searches = [
    ("Software Engineer", "India"),
    ("Product Designer", "India"),
    ("Game Developer", "India"),
    ("Civil Engineer", "United Arab Emirates"),
    ("Electrical Engineer", "India"),
    ("Investment Banking", "Bengaluru"),
    ("Talent Acquisition", "India"),
    ("Software Engineer", "Dubai"),
    ("Construction Engineer", "Dubai")
]

total = 0
for kw, loc in searches:
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={httpx.URL(kw).raw_path.decode()}&location={httpx.URL(loc).raw_path.decode()}&start=0"
    try:
        r = httpx.get(url, headers=headers, timeout=10.0)
        cards = re.findall(r'<div class="base-card[^"]*"(.*?)</li>', r.text, re.DOTALL)
        print(f"LinkedIn [{kw} in {loc}]: {r.status_code} -> {len(cards)} jobs")
        total += len(cards)
        time.sleep(1)
    except Exception as e:
        print(f"Error on {kw}: {e}")

print(f"Total LinkedIn roles found across domains: {total}")
