import httpx
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml"
}

try:
    r = httpx.get("https://in.indeed.com/jobs?q=software+engineer&l=Bengaluru", headers=headers, timeout=10.0)
    print("Indeed status:", r.status_code)
    # Check for job keys in mosaic data
    jobkeys = re.findall(r'jk=([a-f0-9]{16})', r.text)
    print("Indeed jobkeys found:", len(set(jobkeys)))
    for jk in list(set(jobkeys))[:5]:
        print(f"  Indeed job: https://in.indeed.com/viewjob?jk={jk}")
except Exception as e:
    print("Indeed err:", e)
