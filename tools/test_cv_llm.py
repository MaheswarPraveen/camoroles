import urllib.request
import json

import os
or_key = os.environ.get('OPENROUTER_API_KEY', '')  # never hard-code keys

cv_sample = """
Jane Doe - Lead Distributed Systems Engineer
San Francisco, CA | jane@example.com
Experience:
- Senior Staff Software Engineer at Stripe (2020 - Present, 4 yrs): Built high throughput payment settlement engines in Go and C++. Optimized Kafka pipelines handling 500k events/sec.
- Senior Backend Developer at Datadog (2017 - 2020, 3 yrs): Designed distributed tracing microservices with Kubernetes, gRPC, and Redis.
Skills: Go, C++, Kubernetes, Kafka, Distributed Systems, Redis, Docker, PostgreSQL
"""

system_prompt = """You are an elite talent recruiter and CV parser.
Extract the candidate profile from the text and output ONLY valid JSON matching this schema:
{
  "headline": "Candidate Headline",
  "experienceYears": 7,
  "skills": ["Skill1", "Skill2", "Skill3"],
  "discipline": "choice among: ai, backend, spacetech, robotics, defense_cyber, devops, frontend, hardware, trading",
  "summary": "2 sentence executive candidate summary"
}
No markdown backticks, no prose, no emojis."""

req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
    data=json.dumps({
        'model': 'meta-llama/llama-3.3-70b-instruct',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': cv_sample}
        ],
        'temperature': 0.1,
        'max_tokens': 300
    }).encode(),
    headers={'Authorization': f'Bearer {or_key}', 'Content-Type': 'application/json'}
)

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    raw = data['choices'][0]['message']['content']
    print('Raw response:\n', raw)
