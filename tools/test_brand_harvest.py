import httpx
import re
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

queries = [
    ("NVIDIA", "Santa Clara, California, United States"),
    ("NVIDIA", "Bengaluru, Karnataka, India"),
    ("Apple", "Cupertino, California, United States"),
    ("Apple", "Hyderabad, Telangana, India"),
    ("Tesla", "Palo Alto, California, United States"),
    ("Tesla", "Austin, Texas, United States"),
    ("Google", "Mountain View, California, United States"),
    ("Google", "Bengaluru, Karnataka, India"),
    ("Microsoft", "Redmond, Washington, United States"),
    ("Microsoft", "Hyderabad, Telangana, India")
]

for brand, loc in queries:
    kw_enc = brand.replace(" ", "%20")
    loc_enc = loc.replace(" ", "%20").replace(",", "%2C")
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={kw_enc}&location={loc_enc}&start=0"
    try:
        r = httpx.get(url, headers=headers, timeout=12.0)
        cards = re.findall(r'<div class="base-card[^"]*"(.*?)</li>', r.text, re.DOTALL)
        print(f"[{brand} in {loc}] -> {len(cards)} cards (Status: {r.status_code})")
        for c in cards[:2]:
            t_m = re.search(r'<h3 class="base-search-card__title">[\s\n]*(.*?)[\s\n]*</h3>', c)
            c_m = re.search(r'<h4 class="base-search-card__subtitle">[\s\n]*(?:<a[^>]*>)?[\s\n]*(.*?)[\s\n]*(?:</a>)?[\s\n]*</h4>', c)
            l_m = re.search(r'<a class="base-card__full-link[^"]*" href="([^"]+)"', c)
            t = t_m.group(1).strip() if t_m else ""
            comp = re.sub(r'<[^>]+>', '', c_m.group(1)).strip() if c_m else ""
            link = l_m.group(1).split("?")[0].strip() if l_m else ""
            print(f"   * {t} | {comp} | {link}")
    except Exception as e:
        print(f"Error {brand}: {e}")
    time.sleep(1.0)
