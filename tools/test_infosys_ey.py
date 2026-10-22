import httpx
import re

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
rm = httpx.get("https://career.infosys.com/main.js", headers=headers, timeout=10.0)

matches = [m.start() for m in re.finditer(r'http[s]?://[^"\'\s)]*(?:job|career|search)', rm.text, re.IGNORECASE)]
print("Found URLs:", len(matches))
urls = set()
for idx in matches:
    u = rm.text[idx:idx+100].split('"')[0].split("'")[0].split(')')[0].split('`')[0]
    urls.add(u)
print("Unique URLs:", urls)
