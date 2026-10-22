import urllib.request, json

req = urllib.request.Request('https://camouroles.primemax.workers.dev/api/jobs', headers={'User-Agent': 'Mozilla/5.0'})
data = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
jobs = data.get('jobs', [])

for comp in ['nvidia', 'apple', 'meta', 'microsoft', 'google']:
    c_jobs = [j for j in jobs if comp in j.get('company', '').lower()]
    print(f"=== {comp.upper()} (Total: {len(c_jobs)}) ===")
    for j in c_jobs[:5]:
        apply_url = j.get('applyUrl') or ''
        print(f"  Title: {j.get('title')} | Portal: {j.get('portal')} | URL: {apply_url[:80]}")
