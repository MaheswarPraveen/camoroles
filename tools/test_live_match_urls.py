import urllib.request, json

payload = {
    'fileName': 'engineer_cv.pdf',
    'cvText': '''
Alex Mercer - Senior Distributed Systems & Cloud Engineer
Summary: 6 years of experience building scalable backend microservices, distributed data processing, and Kubernetes infrastructure in Python, Go, and C++.
Skills: Python, Go, Docker, Kubernetes, AWS, PostgreSQL, Distributed Systems, Linux, C++, Microservices.
Experience:
Senior Software Engineer at DataCorp (2022-Present): Designed high-throughput gRPC services, reduced latency by 35%, deployed on EKS.
Software Engineer at CloudTech (2019-2022): Built distributed pipelines in Python and PostgreSQL.
'''
}

req = urllib.request.Request(
    'https://camouroles.primemax.workers.dev/api/cv-match',
    data=json.dumps(payload).encode('utf-8'),
    headers={
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
)

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    top_jobs = data.get('top_jobs', [])
    matches = data.get('matches', {})

req_jobs = urllib.request.Request(
    'https://camouroles.primemax.workers.dev/api/jobs',
    headers={'User-Agent': 'Mozilla/5.0'}
)
with urllib.request.urlopen(req_jobs) as r:
    jdata = json.loads(r.read().decode('utf-8'))
    jmap = {j['id']: j for j in jdata.get('jobs', [])}

print("Top 10 Matched Jobs (Strictly Top 50, No Paralegals, Direct ATS):")
for jid in top_jobs[:10]:
    job = jmap.get(jid, {})
    match_info = matches.get(jid, {})
    title = job.get('title')
    company = job.get('company')
    score = match_info.get('score')
    url = job.get('applyUrl', '')[:70]
    print(f"- {title} @ {company} | Score: {score}% | URL: {url}")
