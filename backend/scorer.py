from typing import Dict, Any
from backend.llm_router import LLMRouter

MATCH_RUBRIC_PROMPT = """
You are an objective hiring evaluator for Indian tech startups and mid-market firms.
Compare a candidate's background against a specific job role.

Return ONLY a valid JSON object matching this schema:
{
  "match_score": 82, // integer 1 to 100.
  "why_matched": "Line 1 explaining exact stack/project overlap.\nLine 2 explaining seniority/fresher fit or key requirement."
}

Rules:
1. 'match_score' must reflect actual skill & experience alignment:
   - 80-99: Strong match on primary technologies and experience level.
   - 65-79: Good potential; matching core language but missing 1 secondary tool.
   - <60: Mismatch in core stack or seniority gap.
2. 'why_matched' must be EXACTLY TWO LINES separated by a newline:
   - Specific to the technologies and candidate's projects.
   - No fluff, no generic pleasantries like 'This is a great opportunity'.
"""

def evaluate_match(candidate: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates a candidate against a job role.
    Returns:
    {
       "match_score": int (1-100),
       "why_matched": str (two lines)
    }
    """
    prompt_user = f"""
CANDIDATE:
- Headline: {candidate.get('headline')}
- Experience: {candidate.get('experience_years', 0)} years
- Skills: {', '.join(candidate.get('skills', []))}
- Summary: {candidate.get('summary')}

JOB:
- Title: {job.get('title')}
- Company: {job.get('company')}
- Experience Needed: {job.get('experience_min', 0)} - {job.get('experience_max', 3)} years
- Required Skills: {', '.join(job.get('skills', []))}
- Description: {job.get('description', '')[:2000]}
"""

    messages = [
        {"role": "system", "content": MATCH_RUBRIC_PROMPT},
        {"role": "user", "content": prompt_user}
    ]

    res = LLMRouter.chat_json(messages)
    score = int(res.get("match_score", 50))
    why = str(res.get("why_matched", "")).strip()

    # Ensure two lines
    lines = [l.strip() for l in why.split("\n") if l.strip()]
    if len(lines) >= 2:
        clean_why = f"{lines[0]}\n{lines[1]}"
    elif len(lines) == 1:
        clean_why = f"{lines[0]}\nMatches required core foundation."
    else:
        clean_why = "Core skills align with the primary job requirements.\nMatches the experience target for this position."

    return {
        "match_score": max(1, min(100, score)),
        "why_matched": clean_why
    }
