import httpx
import html
import json
import re

urls = [
    'https://www.ycombinator.com/jobs/role/eng',
    'https://www.ycombinator.com/jobs/location/remote'
]

for url in urls:
    r = httpx.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    m = re.search(r'data-page="([^"]+)"', r.text)
    if m:
        data = json.loads(html.unescape(m.group(1)))
        postings = data.get('props', {}).get('jobPostings', [])
        print(f"{url} -> {r.status_code} | {len(postings)} postings found!")
        for p in postings[:3]:
            print(f"   [{p.get('companyName')}] {p.get('title')} ({p.get('location')}) - {p.get('salaryRange')}")
    else:
        print(f"{url} -> {r.status_code} | No data-page found")
