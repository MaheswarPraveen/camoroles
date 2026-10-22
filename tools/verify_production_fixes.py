import httpx
import json

BASE = 'https://camouroles.primemax.workers.dev'
client = httpx.Client(timeout=25.0)

print('=== 1. TEST /api/geo ===')
r = client.get(f'{BASE}/api/geo')
print('Status:', r.status_code)
print('Payload:', r.json())
print('Cache-Control:', r.headers.get('cache-control'))

print('\n=== 2. TEST /api/jobs CACHE & COMPANY SANITIZATION ===')
r = client.get(f'{BASE}/api/jobs')
print('Status:', r.status_code)
print('Cache-Control:', r.headers.get('cache-control'))
data = r.json()
jobs = data.get('jobs', [])
print('Total verified jobs in catalog:', len(jobs))
generic_found = [j for j in jobs if (j.get('company') or '').lower() in ['startup', 'company', 'confidential', 'stealth']]
print('Generic/Startup companies in catalog:', len(generic_found))

print('\n=== 3. TEST /api/profile UNAUTHENTICATED ===')
r = client.get(f'{BASE}/api/profile')
p_data = r.json()
print('Authenticated:', p_data.get('authenticated'))
print('Is Unlimited:', p_data.get('is_unlimited'))
print('Profile:', p_data.get('profile'))
print('Free Unlocks Left:', p_data.get('free_unlocks_left'))

print('\n=== 4. TEST /api/ai/recruiter_chat (2 YOE Robotics & AI candidate in India) ===')
req_body = {
    'message': 'can I get in india?',
    'conversation': [
        {'role': 'assistant', 'content': 'Welcome. What challenges are you looking to tackle next?'},
        {'role': 'user', 'content': 'Recommend top matching roles for my CV: Forward Deployed Engineer (Robotics & AI) with skills in Python, C/C++, ROS2, LLMs'}
    ],
    'profile': {
        'headline': 'Forward Deployed Engineer (Robotics & AI)',
        'experienceYears': 2,
        'experienceText': '2+ yrs verified experience',
        'skills': ['Python', 'C/C++', 'ROS2', 'Robotics', 'Conversational AI'],
        'discipline': 'robotics'
    },
    'session_state': {
        'discipline': 'robotics',
        'location': 'all',
        'minExp': 2
    }
}
r = client.post(f'{BASE}/api/ai/recruiter_chat', json=req_body)
chat_res = r.json()
print('Reply text:\n', chat_res.get('reply'))
print('\nFilters:', chat_res.get('filters'))
print('Session State:', chat_res.get('session_state'))
matched_ids = chat_res.get('matched_job_ids', [])
job_map = {j['id']: j for j in jobs}
matched_sample = [job_map[jid] for jid in matched_ids[:5] if jid in job_map]

print('\nTop Matched Cards returned:')
for j in matched_sample:
    print('  -', j.get('company'), '|', j.get('title'), f"({j.get('minExp', 0)}-{j.get('maxExp', 0)} yrs)", '|', j.get('location'))

has_intern = any('intern' in (j.get('title') or '').lower() or 'fellow' in (j.get('title') or '').lower() for j in matched_sample)
has_senior = any('senior' in (j.get('title') or '').lower() or 'lead' in (j.get('title') or '').lower() or j.get('minExp', 0) >= 5 for j in matched_sample)
has_fincrime = any('fincrime' in (j.get('title') or '').lower() or 'compliance' in (j.get('title') or '').lower() for j in matched_sample)

print('\nVerification Checks:')
print(f'Intern / Fellowship present: {has_intern}')
print(f'Senior / Lead present: {has_senior}')
print(f'FinCrime / Compliance present: {has_fincrime}')

print('\n=== 5. TEST /api/ai/recruiter_chat (Positive match: Remote Robotics & AI) ===')
req_body_remote = {
    'message': 'show me remote robotics engineering positions',
    'conversation': [],
    'profile': {
        'headline': 'Forward Deployed Engineer (Robotics & AI)',
        'experienceYears': 2,
        'experienceText': '2+ yrs verified experience',
        'skills': ['Python', 'C/C++', 'ROS2', 'Robotics'],
        'discipline': 'robotics'
    },
    'session_state': {
        'discipline': 'robotics',
        'location': 'worldwide_remote',
        'minExp': 2
    }
}
r2 = client.post(f'{BASE}/api/ai/recruiter_chat', json=req_body_remote)
chat_res2 = r2.json()
print('Reply text:\n', chat_res2.get('reply'))
matched_ids2 = chat_res2.get('matched_job_ids', [])
matched_sample2 = [job_map[jid] for jid in matched_ids2[:5] if jid in job_map]

print('\nTop Matched Cards returned:')
for j in matched_sample2:
    print('  -', j.get('company'), '|', j.get('title'), f"({j.get('minExp', 0)}-{j.get('maxExp', 0)} yrs)", '|', j.get('location'))

has_intern2 = any('intern' in (j.get('title') or '').lower() or 'fellow' in (j.get('title') or '').lower() for j in matched_sample2)
has_senior2 = any('senior' in (j.get('title') or '').lower() or 'lead' in (j.get('title') or '').lower() or j.get('minExp', 0) >= 5 for j in matched_sample2)

print(f'\nIntern / Fellowship present: {has_intern2}')
print(f'Senior / Lead present: {has_senior2}')

