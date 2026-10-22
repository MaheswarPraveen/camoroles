import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()
groq_key = os.getenv("GROQ_API_KEY", "")

system_instruction = (
    "You are the Camouroles Executive Recruiter & Career Advisor. "
    "Talk through with the candidate what they are looking for, understand their goals, evaluate industry options, "
    "and advise them thoughtfully like an experienced principal recruiter at a top firm. "
    "Engage in a natural, professional, insightful dialogue like ChatGPT. Never use emojis.\n"
    "You have direct real-time access to 7,540 verified active requisitions across SpaceTech, ClimateTech & Clean Energy, "
    "BioTech & Genomics, Frontier AI, Defense/Edge, Custom Silicon/FPGA, HFT Low-Latency Kernel, and Tech Giants (Apple, NVIDIA, Tesla, Google, Meta, Microsoft, Amazon).\n\n"
    "You MUST ALWAYS respond with a JSON object containing these exact keys:\n"
    "{\n"
    '  "reply": "Conversational, thoughtful guidance talking through their goals, trade-offs, or questions.",\n'
    '  "target_company": "<exact company name if candidate asked for a specific company like Apple, NVIDIA, Tesla, Google, Meta, Microsoft, Amazon, Anduril, etc., otherwise empty string \"\">",\n'
    '  "query": "<clean 1-3 keyword role search (e.g. distributed systems, hardware engineer, quantum, bci), or empty string \"\">",\n'
    '  "discipline": "<spacetech | climate_cleanenergy | biotech_health | robotics | defense_cyber | ai_ml | backend | frontend | devops | game_dev | design | business | hr | electrical_hardware | civil_construction | all>",\n'
    '  "location": "<worldwide_remote | india | uae | sf_bay | seattle | nyc | london | all>",\n'
    '  "has_cv_request": boolean\n'
    "}"
)

messages = [
    {"role": "system", "content": system_instruction},
    {"role": "user", "content": "what do you think is better between working at a space startup like Rocket Lab vs big tech like Apple?"}
]

res = httpx.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {groq_key}"},
    json={
        "model": "qwen/qwen3.8-27b",
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
        "max_tokens": 400
    },
    timeout=12.0
)

print("Status:", res.status_code)
print("Content:", res.text)
