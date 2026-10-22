import urllib.request
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

print('=== 1. PAGES VERIFICATION ===')
req_page = urllib.request.Request('https://camouroles.pages.dev', headers=headers)
html = urllib.request.urlopen(req_page).read().decode('utf-8')
print('CAMOUROLES in title:', '<title>CAMOUROLES' in html)
print('Search bar text:', 'Click here to match using talent intelligence' in html)

print('\n=== 2. HONEST ZERO RESULTS CHAT ===')
url_chat = 'https://camouroles.primemax.workers.dev/api/ai/recruiter_chat'
payload_zero = {
    'message': 'are there any quantum computing jobs in dubai?',
    'conversation': [],
    'profile': {'headline': 'Quantum Engineer', 'discipline': 'quantum', 'skills': ['Qiskit']}
}
req_zero = urllib.request.Request(url_chat, data=json.dumps(payload_zero).encode('utf-8'), headers={'Content-Type': 'application/json', **headers})
res_zero = json.loads(urllib.request.urlopen(req_zero).read().decode('utf-8'))
print('Zero match reply:', res_zero.get('reply'))
print('Zero match total_matched:', res_zero.get('total_matched'))

print('\n=== 3. DISCIPLINE PIVOT & NON-TECH EXCLUSION ===')
payload_pivot = {
    'message': 'what about backend remote jobs?',
    'conversation': [{'role': 'user', 'content': 'can we have some remote jobs?'}],
    'profile': {'headline': 'Robotics Engineer', 'discipline': 'robotics', 'skills': ['Python', 'ROS 2']}
}
req_pivot = urllib.request.Request(url_chat, data=json.dumps(payload_pivot).encode('utf-8'), headers={'Content-Type': 'application/json', **headers})
res_pivot = json.loads(urllib.request.urlopen(req_pivot).read().decode('utf-8'))
print('Pivot reply:', res_pivot.get('reply'))
print('Pivot total_matched:', res_pivot.get('total_matched'))
print('Pivot matched_job_ids count:', len(res_pivot.get('matched_job_ids', [])))

print('\n=== 4. CV MATCHING ACCURACY ===')
url_jobs = 'https://camouroles.primemax.workers.dev/api/jobs'
req_j = urllib.request.Request(url_jobs, headers=headers)
jobs_data = json.loads(urllib.request.urlopen(req_j).read().decode('utf-8'))
jobs_by_id = {j['id']: j for j in jobs_data.get('jobs', [])}

url_cv = 'https://camouroles.primemax.workers.dev/api/cv/match'
cv_text = '''
Maheswar Praveen
Robotics and AI Research Engineer (1+ yrs experience)
Skills: Python, C/C++, JavaScript, Kotlin, ROS 2, ArduPilot, TensorFlow, PyTorch, OpenCV, ESP32, Arduino.
Autonomous farming rovers, robotic arms, computer vision, kinematics, SLAM.
'''
payload_cv = {'cv_text': cv_text, 'file_name': 'Maheswar_CV.pdf'}
req_cv = urllib.request.Request(url_cv, data=json.dumps(payload_cv).encode('utf-8'), headers={'Content-Type': 'application/json', **headers})
res_cv = json.loads(urllib.request.urlopen(req_cv).read().decode('utf-8'))
matches = res_cv.get('matches', {})
sorted_matches = sorted(matches.items(), key=lambda x: x[1].get('score', 0), reverse=True)
print(f'Total matched jobs: {len(sorted_matches)}')
for jid, m in sorted_matches[:5]:
    job = jobs_by_id.get(jid, {})
    score = m.get('score')
    title = job.get('title')
    company = job.get('company')
    discipline = job.get('discipline')
    exp = job.get('expText')
    print(f' - Score {score}%: {title} at {company} (Exp: {exp}, Discipline: {discipline})')

