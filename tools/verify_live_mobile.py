import urllib.request
import json
import time

print("--- 1. Testing Worker API (https://camouroles.primemax.workers.dev/api/jobs) ---")
start = time.time()
req = urllib.request.Request('https://camouroles.primemax.workers.dev/api/jobs', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    headers = dict(resp.getheaders())
    body = resp.read()
duration = time.time() - start

print(f"Status Code: {resp.status}")
print(f"Latency: {duration*1000:.1f}ms")
print(f"Cache-Control: {headers.get('cache-control')}")
print(f"CDN-Cache-Control: {headers.get('cdn-cache-control')}")

data = json.loads(body.decode())
total = data.get('totalVerified')
jobs = data.get('jobs', [])
print(f"Total Verified: {total} | Array Length: {len(jobs)}")

safety_roles = [
    j for j in jobs
    if j.get('discipline') == 'safety'
    or 'safety' in j.get('title', '').lower()
    or 'fire' in j.get('title', '').lower()
    or any('safety' in str(s).lower() for s in (j.get('skills') or []))
]
print(f"Safety & Fire Engineering Roles: {len(safety_roles)}")
for role in safety_roles[:4]:
    print(f"  • {role.get('company')} | {role.get('title')} | {role.get('location')} | {role.get('discipline')}")

france_roles = [
    j for j in jobs
    if 'france' in (j.get('location') or '').lower() or 'paris' in (j.get('location') or '').lower()
]
print(f"France / Paris Roles: {len(france_roles)}")

print("\n--- 2. Testing Pages Web Frontend (https://camouroles.pages.dev) ---")
req_pages = urllib.request.Request('https://camouroles.pages.dev', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req_pages) as resp_p:
    pages_html = resp_p.read().decode('utf-8', errors='ignore')

has_safety_desktop = 'data-discipline="safety"' in pages_html
has_france_desktop = 'data-location="france"' in pages_html
has_view_all = 'View All 10,237' in pages_html
has_mobile_filter = 'mobile-filter-modal' in pages_html
has_mobile_chips = 'pref-chip' in pages_html

print(f"Desktop & Mobile Safety Chip: {has_safety_desktop}")
print(f"Desktop & Mobile France Chip: {has_france_desktop}")
print(f"View All 10,237 Escape CTA: {has_view_all}")
print(f"Mobile Filter Modal: {has_mobile_filter}")
print(f"Mobile Chips Present: {has_mobile_chips}")

print("\n--- 3. Testing Live CSS (https://camouroles.pages.dev/styles.css) ---")
req_css = urllib.request.Request('https://camouroles.pages.dev/styles.css', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req_css) as resp_c:
    css_content = resp_c.read().decode('utf-8', errors='ignore')

has_ios_zoom_fix = '16px !important' in css_content
has_safe_area = 'safe-area-inset-bottom' in css_content
has_feed_view_all = '.feed-view-all-link' in css_content
print(f"iOS Safari Auto-Zoom Fix (16px inputs): {has_ios_zoom_fix}")
print(f"Touch Target & Safe Area Insets: {has_safe_area}")
print(f"Feed View All Link CSS: {has_feed_view_all}")
