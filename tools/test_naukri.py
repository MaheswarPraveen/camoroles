import httpx
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml"
}

r = httpx.get("https://www.naukri.com/software-engineer-jobs-in-bangalore", headers=headers, timeout=10.0)
scripts = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.DOTALL)
print("Found scripts:", len(scripts))
for i, s in enumerate(scripts):
    s_clean = s.strip()
    if s_clean and ("self.__next_f" in s_clean or "job" in s_clean.lower()):
        print(f"Script {i} ({len(s_clean)} chars):", s_clean[:300])
