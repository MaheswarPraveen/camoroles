import urllib.request, json, re

req = urllib.request.Request('https://camouroles.primemax.workers.dev/api/jobs', headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req)
jobs = json.loads(resp.read().decode('utf-8')).get('jobs', [])

profile = {
    'headline': 'Robotics and AI Research Engineer',
    'experienceYears': 1,
    'skills': ['Python', 'C/C++', 'ROS 2', 'ArduPilot', 'OpenCV'],
    'discipline': 'robotics'
}

DISCIPLINE_DOMAIN_KEYWORDS = {
    'robotics': r'\b(robot|robotics|autonomy|autonomous|uav|drone|ros|ros2|slam|ardupilot|px4|mechatronics|kinematics|perception|motion planning|controls)\b',
    'frontend': r'\b(frontend|front[- ]end|react|vue|angular|svelte|web developer|javascript|typescript|ui|ux)\b',
    'backend': r'\b(backend|back[- ]end|golang|rust|distributed systems|microservices|cloud|server|database|infra)\b',
    'ai': r'\b(ai|artificial intelligence|machine learning|deep learning|llm|computer vision|nlp|neural|genai)\b',
    'trading': r'\b(trading|quant|hft|low latency|market making|order book)\b',
    'hardware': r'\b(hardware|asic|fpga|silicon|rtl|soc|risc-v|semiconductor|vlsi)\b'
}

NON_TECH = [
    r'\bparalegal\b', r'\blegal\b', r'\bcounsel\b', r'\battorney\b', r'\blawyer\b',
    r'\bcompliance\b', r'\brecruiter\b', r'\brecruiting\b', r'\btalent\b', r'\bsourcer\b',
    r'\bhuman resources\b', r'\bhr\b', r'\bcoordinator\b', r'\baccountant\b', r'\baccounting\b',
    r'\bbookkeeper\b', r'\bpayroll\b', r'\bcontroller\b', r'\btreasury\b', r'\bfinance\b',
    r'\bsales\b', r'\bmarketing\b', r'\baccount executive\b', r'\bbusiness development\b',
    r'\bretail\b'
]

scored = []
cand_disc = profile['discipline']
disc_rx = re.compile(DISCIPLINE_DOMAIN_KEYWORDS.get(cand_disc, ''), re.I)

for j in jobs:
    t = (j.get('title') or '').lower()
    c = (j.get('company') or '').lower()
    skills = [str(s).lower() for s in (j.get('skills') or [])]
    min_exp = j.get('minExp') or 0
    max_exp = j.get('maxExp') or 10

    if any(re.search(rx, t) for rx in NON_TECH):
        continue

    score = 0
    reasons = []

    # 1. Discipline & Domain (up to 35 pts)
    if j.get('discipline') == cand_disc or disc_rx.search(t):
        score += 35
        reasons.append('Direct domain')
    elif cand_disc == 'robotics' and (j.get('discipline') in ['ai', 'hardware'] or any(k in t for k in ['computer vision', 'embedded', 'firmware', 'controls'])):
        score += 18
        reasons.append('Adjacent field')
    elif j.get('discipline') != cand_disc:
        score += 0

    # 2. Domain Title match (up to 30 pts)
    if re.search(r'\b(robot|robotics|autonomy|autonomous|ros|slam|ardupilot|uav|drone)\b', t):
        score += 30
        reasons.append('Role title')
    elif re.search(r'\b(computer vision|perception|controls|embedded software)\b', t):
        score += 20
        reasons.append('Specialization')

    # 3. Skills match (up to 25 pts)
    matched_skills = []
    for s in profile['skills']:
        s_clean = s.lower().strip()
        if s_clean in ['c', 'c++', 'c/c++']:
            if any(re.search(r'\b(c\+\+|cpp|c)\b', js) for js in skills) or re.search(r'\b(c\+\+|cpp)\b', t):
                matched_skills.append('C++')
        else:
            if any(s_clean in js for js in skills) or s_clean in t:
                matched_skills.append(s)

    if matched_skills:
        score += min(25, len(matched_skills) * 8)
        reasons.append('Skills: ' + ', '.join(list(set(matched_skills))[:3]))

    # 4. Seniority / Experience fit
    is_exec = bool(re.search(r'\b(director|vp|head of|principal|chief)\b', t))
    if is_exec:
        score -= 25
    elif profile['experienceYears'] >= min_exp and profile['experienceYears'] <= max_exp:
        score += 10
    elif abs(profile['experienceYears'] - min_exp) <= 2:
        score += 5

    if score >= 45:
        final_score = min(96, max(55, score))
        scored.append((final_score, j.get('title'), j.get('company'), j.get('location'), reasons))

scored.sort(key=lambda x: -x[0])
print(f'Total accurate matches found: {len(scored)}')
print('Top 15 matches:')
for s, title, comp, loc, reasons in scored[:15]:
    reason_str = ' · '.join(reasons)
    print(f'[{s}%] {title} @ {comp} ({loc}) -> {reason_str}')
