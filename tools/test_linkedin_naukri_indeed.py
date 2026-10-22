import httpx
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

# 1. LinkedIn
print("--- TESTING LINKEDIN ---")
try:
    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Software%20Engineer&location=India&start=0"
    r = httpx.get(url, headers=headers, timeout=10.0)
    print("LinkedIn status:", r.status_code)
    # Parse cards
    cards = re.findall(r'<div class="base-card[^"]*"(.*?)</li>', r.text, re.DOTALL)
    print("Found cards:", len(cards))
    for c in cards[:5]:
        t_m = re.search(r'<h3 class="base-search-card__title">[\s\n]*(.*?)[\s\n]*</h3>', c)
        comp_m = re.search(r'<h4 class="base-search-card__subtitle">[\s\n]*(?:<a[^>]*>)?[\s\n]*(.*?)[\s\n]*(?:</a>)?[\s\n]*</h4>', c)
        loc_m = re.search(r'<span class="job-search-card__location">[\s\n]*(.*?)[\s\n]*</span>', c)
        link_m = re.search(r'<a class="base-card__full-link[^"]*" href="([^"]+)"', c)
        title = t_m.group(1).strip() if t_m else "Role"
        comp = re.sub(r'<[^>]+>', '', comp_m.group(1)).strip() if comp_m else "Company"
        loc = loc_m.group(1).strip() if loc_m else "India"
        link = link_m.group(1).split("?")[0].strip() if link_m else "https://www.linkedin.com/jobs"
        print(f"  [LI] {title} at {comp} ({loc}) -> {link}")
except Exception as e:
    print("LinkedIn err:", e)

# 2. Indeed
print("\n--- TESTING INDEED ---")
try:
    # Indeed RSS feeds:
    for feed_url in ["https://www.indeed.com/rss?q=software+engineer&l=remote", "https://in.indeed.com/rss?q=software+engineer&l=Bengaluru"]:
        r_ind = httpx.get(feed_url, headers=headers, timeout=10.0)
        print(f"Indeed status ({feed_url[:30]}):", r_ind.status_code)
        items = re.findall(r'<item>(.*?)</item>', r_ind.text, re.DOTALL)
        print("  Items found:", len(items))
        for item in items[:3]:
            title_m = re.search(r'<title>(.*?)</title>', item)
            link_m = re.search(r'<link>(.*?)</link>', item)
            source_m = re.search(r'<source[^>]*>(.*?)</source>', item)
            print("  [Indeed]", title_m.group(1) if title_m else "", "->", link_m.group(1) if link_m else "")
except Exception as e:
    print("Indeed err:", e)

# 3. Naukri
print("\n--- TESTING NAUKRI ---")
try:
    naukri_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "appid": "109",
        "systemid": "Naukri",
        "clientid": "d3skt0p"
    }
    r_nk = httpx.get("https://www.naukri.com/jobapi/v3/search?noOfResults=20&urlType=search_by_keyword&searchType=adv&keyword=software%20engineer&location=bangalore", headers=naukri_headers, timeout=10.0)
    print("Naukri status:", r_nk.status_code)
    if r_nk.status_code == 200:
        nk_data = r_nk.json()
        job_details = nk_data.get("jobDetails", [])
        print("Naukri jobs found:", len(job_details))
        for j in job_details[:5]:
            title = j.get("title")
            comp = j.get("companyName")
            loc = j.get("placeholders", [{}])[0].get("label") if j.get("placeholders") else "Bengaluru"
            jid = j.get("jobId")
            url = f"https://www.naukri.com/job-listings-{jid}" if jid else j.get("jdURL", "https://www.naukri.com")
            print(f"  [Naukri] {title} at {comp} ({loc}) -> {url}")
except Exception as e:
    print("Naukri err:", e)
