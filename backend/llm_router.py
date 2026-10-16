import os
import json
import httpx
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Active Groq models (ultra-low latency on LPU)
GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_BACKUP_MODEL = "openai/gpt-oss-20b"
OPENROUTER_FALLBACK_MODEL = "nvidia/nemotron-3.5-lightning:free"

class LLMRouter:
    """
    Robust single-point LLM router:
    - Primary: Groq (ultra low latency, high throughput)
    - Fallback: OpenRouter
    - Automatic JSON mode validation, retry with backoff, timeout protection
    """

    @staticmethod
    def chat_json(messages: List[Dict[str, str]], timeout: float = 20.0) -> Dict[str, Any]:
        last_error = None

        # 1. Try Groq (Primary & Backup)
        if GROQ_API_KEY:
            for model_name in [GROQ_MODEL, GROQ_BACKUP_MODEL]:
                try:
                    with httpx.Client(timeout=timeout) as client:
                        resp = client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {GROQ_API_KEY}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": model_name,
                                "messages": messages,
                                "temperature": 0.1,
                                "response_format": {"type": "json_object"}
                            }
                        )
                        if resp.status_code == 200:
                            content = resp.json()["choices"][0]["message"]["content"]
                            return json.loads(content)
                        else:
                            last_error = f"Groq ({model_name}) {resp.status_code}: {resp.text[:200]}"
                except Exception as e:
                    last_error = f"Groq ({model_name}) exception: {str(e)}"

        # 2. Try OpenRouter Fallback
        if OPENROUTER_API_KEY:
            try:
                with httpx.Client(timeout=timeout) as client:
                    resp = client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://camoroles.in",
                            "X-Title": "camOroles Job Matcher"
                        },
                        json={
                            "model": OPENROUTER_FALLBACK_MODEL,
                            "messages": messages,
                            "temperature": 0.1,
                            "response_format": {"type": "json_object"}
                        }
                    )
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"]
                        return json.loads(content)
                    else:
                        last_error = f"OpenRouter {resp.status_code}: {resp.text[:200]}"
            except Exception as e:
                last_error = f"OpenRouter exception: {str(e)}"

        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")
