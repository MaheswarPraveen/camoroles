import httpx
import re

url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Software%20Engineer&location=India&start=0"
r = httpx.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
links = re.findall(r'href="([^"]+)"', r.text)
job_links = [l.split("?")[0] for l in links if "linkedin.com/jobs/view" in l]
print(f"Total found: {len(job_links)}")
for l in job_links[:5]:
    print(l)
