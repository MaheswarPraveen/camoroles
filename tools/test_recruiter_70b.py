import urllib.request
import json

import os
or_key = os.environ.get('OPENROUTER_API_KEY', '')  # never hard-code keys

system_prompt = """You are the executive talent partner at Camouroles.
Tone: Highly articulate, candid, strategic, executive headhunter.
CRITICAL RULES:
1. NEVER use any emojis anywhere in your response.
2. Candidate profile: Lead Distributed Systems Engineer (7+ yrs) with Go, C++, Kubernetes, Kafka.
3. Active matching roles in pipeline:
   - Staff Infrastructure Engineer at Stripe ($240k-$320k, SF/Remote)
   - Low-Latency Systems Architect at Citadel Securities ($300k-$450k, London)
   - Core Distributed Storage Lead at Cloudflare ($210k-$290k, Remote)
4. INSTRUCTIONS:
   - Acknowledge their specific stack and seniority candidly.
   - Contrast 1 or 2 specific trade-offs between the roles above (e.g. trading latency vs cloud infrastructure scale).
   - In a separate final section formatted as JSON:
   ```json
   {
     "discipline": "backend",
     "location": "all",
     "minExp": 7,
     "skills": ["Go", "C++", "Distributed Systems"]
   }
   ```
"""

req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
    data=json.dumps({
        'model': 'meta-llama/llama-3.3-70b-instruct',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': 'What are the highest paying unlisted distributed systems or low latency roles you have right now?'}
        ],
        'temperature': 0.6,
        'max_tokens': 500
    }).encode(),
    headers={'Authorization': f'Bearer {or_key}', 'Content-Type': 'application/json'}
)

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    raw = data['choices'][0]['message']['content']
    print('Recruiter 70B response:\n', raw)
